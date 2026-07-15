from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from lookup.serializers import LookupSerializer
from lookup.models import Lookup

class UserSerializer(serializers.ModelSerializer):
    role = LookupSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Lookup.objects.all(),
        source='role',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'full_name', 'date_of_birth', 'role', 'role_id', 'is_approved', 'is_phone_verified', 'is_active', 'created_at')
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    # KYC Fields (Optional for BUYER, Required for others)
    profile_img = serializers.ImageField(required=False)
    nid_number = serializers.CharField(required=False, max_length=50)
    nid_front_image = serializers.ImageField(required=False)
    nid_back_image = serializers.ImageField(required=False)
    birth_certificate_image = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ('phone_number', 'full_name', 'date_of_birth', 'role', 'password', 'confirm_password', 'profile_img', 'nid_number', 'nid_front_image', 'nid_back_image', 'birth_certificate_image')

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
            
        role = data.get('role')
        if role and role.value.upper() != 'BUYER':
            errors = {}
            if not data.get('nid_number'):
                errors['nid_number'] = "NID number is required for this role."
            if not data.get('nid_front_image'):
                errors['nid_front_image'] = "NID front image is required for this role."
            if not data.get('nid_back_image'):
                errors['nid_back_image'] = "NID back image is required for this role."
            
            if errors:
                raise serializers.ValidationError(errors)
                
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Extract KYC data
        kyc_data = {
            'profile_img': validated_data.pop('profile_img', None),
            'nid_number': validated_data.pop('nid_number', None),
            'nid_front_image': validated_data.pop('nid_front_image', None),
            'nid_back_image': validated_data.pop('nid_back_image', None),
            'birth_certificate_image': validated_data.pop('birth_certificate_image', None),
        }
        
        # Check if buyer to auto approve
        role = validated_data.get('role')
        is_approved = False
        if role and role.value.upper() == 'BUYER':
            is_approved = True

        user = User.objects.create_user(
            password=password,
            is_approved=is_approved,
            **validated_data
        )
        
        if role and role.value.upper() != 'BUYER':
            kyc_data = {k: v for k, v in kyc_data.items() if v is not None}
            KYCProfile.objects.create(user=user, **kyc_data)
            
        return user

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}
    )

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        if phone_number and password:
            # Need to authenticate using phone_number
            # Wait, default authenticate uses USERNAME_FIELD
            user = authenticate(request=self.context.get('request'), phone_number=phone_number, password=password)
            if not user:
                raise serializers.ValidationError('Invalid phone number or password.')
                
            if not user.is_phone_verified:
                raise serializers.ValidationError('Your phone number is not verified. Please verify OTP first.')
            
            if not user.is_approved:
                raise serializers.ValidationError('Your account is pending admin approval.')
        else:
            raise serializers.ValidationError('Must include "phone_number" and "password".')
        
        data['user'] = user
        return data

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)

from .models import KYCProfile

class KYCProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = KYCProfile
        fields = ['id', 'user', 'profile_img', 'nid_number', 'nid_front_image', 'nid_back_image', 'birth_certificate_image', 'status', 'submitted_at', 'verified_at']
        read_only_fields = ['id', 'user', 'status', 'submitted_at', 'verified_at']

class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

class KYCProfileBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = ['id', 'profile_img', 'nid_number', 'nid_front_image', 'nid_back_image', 'birth_certificate_image', 'status', 'submitted_at', 'verified_at']
        read_only_fields = ['id', 'status', 'submitted_at', 'verified_at']

class UserWithProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    kyc_profile = KYCProfileBasicSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('user', 'kyc_profile')
        
    def get_user(self, obj):
        return UserSerializer(obj).data



class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
