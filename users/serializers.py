from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from lookup.serializers import LookupSerializer

class UserSerializer(serializers.ModelSerializer):
    role = LookupSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'full_name', 'date_of_birth', 'role', 'is_approved', 'is_active', 'created_at')
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('phone_number', 'full_name', 'date_of_birth', 'role', 'password', 'confirm_password')

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
            
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
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

class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
