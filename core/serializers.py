# core/serializers.py
from rest_framework import serializers
from .models import (
    LearningCenter, Parent, Student, 
    Attendance, Grade, Payment, News
)
from account.models import User


class LearningCenterSerializer(serializers.ModelSerializer):
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningCenter
        fields = [
            'id', 'name', 'address', 'phone_number', 'email',
            'director', 'created_by', 'created_by_info', 'is_active'
        ]
        read_only_fields = ['created_by']
        ref_name = 'CoreLearningCenter'  # Unique ref_name qo'shamiz
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'phone_number': obj.created_by.phone_number,
                'full_name': obj.created_by.full_name,
                'role': obj.created_by.role
            }
        return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class ParentSerializer(serializers.ModelSerializer):
    center_info = LearningCenterSerializer(source='center', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Parent
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 'email',
            'address', 'workplace', 'relationship', 'center', 'center_info',
            'created_by', 'created_by_info', 'is_active'
        ]
        read_only_fields = ['created_by']
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'phone_number': obj.created_by.phone_number,
                'full_name': obj.created_by.full_name,
                'role': obj.created_by.role
            }
        return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
            if request.user.role == 'admin' and not validated_data.get('center'):
                validated_data['center'] = request.user.center
        
        return super().create(validated_data)


class StudentSerializer(serializers.ModelSerializer):
    teacher_info = serializers.SerializerMethodField()
    center_info = LearningCenterSerializer(source='center', read_only=True)
    parent_info = ParentSerializer(source='parent', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'age', 'phone_number',
            'address', 'subject', 'teacher', 'teacher_info', 'center',
            'center_info', 'parent', 'parent_info', 'created_by',
            'created_by_info', 'is_active'
        ]
        read_only_fields = ['created_by']
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'phone_number': obj.teacher.phone_number,
                'full_name': obj.teacher.full_name,
                'role': obj.teacher.role,
                'subject': obj.teacher.subject
            }
        return None
    
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
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'teacher':
                data['teacher'] = request.user
                if not data.get('center'):
                    data['center'] = request.user.center
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
            if request.user.role == 'admin' and not validated_data.get('center'):
                validated_data['center'] = request.user.center
        
        return super().create(validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    student_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_info', 'teacher', 'teacher_info',
            'lesson_1', 'lesson_2', 'lesson_3', 'created_at',
            'created_by', 'created_by_info'
        ]
        read_only_fields = ['created_at', 'created_by']
    
    def get_student_info(self, obj):
        if obj.student:
            return {
                'id': obj.student.id,
                'full_name': obj.student.full_name,
                'subject': obj.student.subject
            }
        return None
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'phone_number': obj.teacher.phone_number,
                'full_name': obj.teacher.full_name
            }
        return None
    
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
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'teacher' and not data.get('teacher'):
                data['teacher'] = request.user
            
            if data.get('student') and data.get('teacher'):
                if request.user.role == 'teacher':
                    if data['student'].teacher != request.user:
                        raise serializers.ValidationError(
                            {"student": "Bu o'quvchi sizga tegishli emas"}
                        )
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class GradeSerializer(serializers.ModelSerializer):
    student_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_info', 'teacher', 'teacher_info',
            'subject', 'score', 'comment', 'date', 'created_by', 'created_by_info'
        ]
        read_only_fields = ['teacher', 'created_by']
    
    def get_student_info(self, obj):
        if obj.student:
            return {
                'id': obj.student.id,
                'full_name': obj.student.full_name,
                'subject': obj.student.subject
            }
        return None
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'phone_number': obj.teacher.phone_number,
                'full_name': obj.teacher.full_name
            }
        return None
    
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
        request = self.context.get('request')
        
        if request and request.user.role == 'teacher':
            student = data.get('student')
            if student and student.teacher != request.user:
                raise serializers.ValidationError(
                    {"student": "Bu o'quvchi sizga tegishli emas"}
                )
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['teacher'] = request.user
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    student_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'student', 'student_info', 'date', 'amount',
            'deadline', 'status', 'created_by', 'created_by_info'
        ]
        read_only_fields = ['created_by']
    
    def get_student_info(self, obj):
        if obj.student:
            return {
                'id': obj.student.id,
                'full_name': obj.student.full_name,
                'subject': obj.student.subject
            }
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'phone_number': obj.created_by.phone_number,
                'full_name': obj.created_by.full_name,
                'role': obj.created_by.role
            }
        return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class NewsSerializer(serializers.ModelSerializer):
    center_info = LearningCenterSerializer(source='center', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'body', 'center', 'center_info',
            'created_by', 'created_by_info', 'created_at', 'is_active'
        ]
        read_only_fields = ['created_at', 'created_by']
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'phone_number': obj.created_by.phone_number,
                'full_name': obj.created_by.full_name,
                'role': obj.created_by.role
            }
        return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
            if request.user.role == 'admin' and not validated_data.get('center'):
                validated_data['center'] = request.user.center
        
        return super().create(validated_data)