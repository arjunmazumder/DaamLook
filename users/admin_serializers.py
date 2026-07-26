from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from .models import User

class AdminLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}
    )

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        if phone_number and password:
            user = authenticate(request=self.context.get('request'), phone_number=phone_number, password=password)
            if not user:
                raise serializers.ValidationError('Invalid phone number or password.')
                
            if not user.is_staff:
                raise serializers.ValidationError('You are not authorized to access the Admin Panel.')
            
            if not user.is_active:
                raise serializers.ValidationError('Your account has been suspended.')
        else:
            raise serializers.ValidationError('Must include "phone_number" and "password".')
        
        data['user'] = user
        return data

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename')

class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        required=False
    )
    permission_details = PermissionSerializer(source='permissions', many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions', 'permission_details')

class StaffSerializer(serializers.ModelSerializer):
    groups = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'phone_number', 'full_name', 'is_staff', 'is_superuser', 'is_active', 'groups', 'created_at')

class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, min_length=6)
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False,
        write_only=True,
        source='groups'
    )

    class Meta:
        model = User
        fields = ('phone_number', 'full_name', 'password', 'group_ids')

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        password = validated_data.pop('password')
        
        # Enforce staff rules
        validated_data['is_staff'] = True
        validated_data['is_approved'] = True
        validated_data['is_phone_verified'] = True
        
        user = User.objects.create_user(password=password, **validated_data)
        
        if groups:
            user.groups.set(groups)
            
        return user
