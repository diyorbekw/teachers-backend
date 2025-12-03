# account/serializers.py
from rest_framework import serializers
from .models import User
from core.models import LearningCenter


# Bu serializer'ni o'zgartiramiz yoki olib tashlaymiz
class LearningCenterShortSerializer(serializers.ModelSerializer):
    """Account app uchun qisqa LearningCenter serializer"""
    class Meta:
        model = LearningCenter
        fields = ['id', 'name', 'address', 'phone_number', 'email', 'director']
        ref_name = 'AccountLearningCenter'  # Unique ref_name qo'shamiz


class UserSerializer(serializers.ModelSerializer):
    # LearningCenterShortSerializer ishlatamiz
    center_info = LearningCenterShortSerializer(source='center', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'role',
            'age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number',
            'center', 'center_info', 'created_by', 'created_by_info',
            'is_active', 'is_staff', 'is_superuser', 'password',
            'last_login', 'date_joined'
        ]
        read_only_fields = ['last_login', 'date_joined', 'created_by']
        extra_kwargs = {
            'phone_number': {'required': True},
            'role': {'required': True}
        }
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'phone_number': obj.created_by.phone_number,
                'full_name': obj.created_by.full_name,
                'role': obj.created_by.role
            }
        return None
    
    def validate(self, data):
        role = data.get('role')
        
        if role == 'teacher':
            required_fields = ['age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number', 'center']
            for field in required_fields:
                if field not in data or data[field] is None:
                    raise serializers.ValidationError(
                        {field: f"Teacher uchun {field} maydoni majburiy"}
                    )
        
        elif role != 'teacher':
            for field in ['age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number']:
                if field in data:
                    data[field] = None
        
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user.created_by = request.user
        
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'phone_number', 'first_name', 'last_name', 'role',
            'age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number',
            'center', 'password', 'password_confirmation'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({"password": "Parollar mos kelmadi"})
        
        role = data.get('role')
        if role == 'teacher':
            required_fields = ['age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number', 'center']
            for field in required_fields:
                if field not in data or data[field] is None:
                    raise serializers.ValidationError(
                        {field: f"Teacher uchun {field} maydoni majburiy"}
                    )
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user.created_by = request.user
        
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'role',
            'age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number',
            'center', 'is_active'
        ]
    
    def validate(self, data):
        role = data.get('role', self.instance.role)
        
        if role == 'teacher':
            instance_data = {**self.instance.__dict__, **data}
            required_fields = ['age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number', 'center']
            for field in required_fields:
                if field not in instance_data or instance_data[field] is None:
                    raise serializers.ValidationError(
                        {field: f"Teacher uchun {field} maydoni majburiy"}
                    )
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "Yangi parollar mos kelmadi"})
        
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "Yangi parol eski paroldan farqli bo'lishi kerak"})
        
        return data