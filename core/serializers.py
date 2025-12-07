# core/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import (
    LearningCenter, Parent, Student, 
    Attendance, Grade, Payment, News, Homework
)
from account.models import User


# ========== Helper Serializers ==========

class UserInfoSerializer(serializers.ModelSerializer):
    """Foydalanuvchi ma'lumotlari uchun qisqa serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'full_name', 'role', 'subject']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class LearningCenterShortSerializer(serializers.ModelSerializer):
    """LearningCenter uchun qisqa serializer"""
    class Meta:
        model = LearningCenter
        fields = ['id', 'name', 'phone_number', 'address']
        read_only_fields = fields


class StudentShortSerializer(serializers.ModelSerializer):
    """Student uchun qisqa serializer"""
    full_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'full_name', 'age', 'subject', 'teacher_name']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_teacher_name(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return None


class ParentShortSerializer(serializers.ModelSerializer):
    """Parent uchun qisqa serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Parent
        fields = ['id', 'first_name', 'last_name', 'full_name', 'phone_number', 'relationship']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# ========== Main Serializers ==========

class LearningCenterSerializer(serializers.ModelSerializer):
    created_by_info = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningCenter
        fields = [
            'id', 'name', 'address', 'phone_number', 'email',
            'director', 'created_by', 'created_by_info', 
            'student_count', 'teacher_count', 'is_active'
        ]
        read_only_fields = ['created_by', 'student_count', 'teacher_count']
        ref_name = 'CoreLearningCenter'
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_student_count(self, obj):
        return Student.objects.filter(center=obj, is_active=True).count()
    
    def get_teacher_count(self, obj):
        return User.objects.filter(center=obj, role="teacher", is_active=True).count()
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)
    
    def validate_phone_number(self, value):
        """Telefon raqamni tekshirish"""
        if not value.startswith('+') and not value.isdigit():
            raise serializers.ValidationError("Telefon raqam noto'g'ri formatda")
        return value
    
    def validate_email(self, value):
        """Email formatini tekshirish"""
        if '@' not in value or '.' not in value.split('@')[-1]:
            raise serializers.ValidationError("Email noto'g'ri formatda")
        return value


class ParentSerializer(serializers.ModelSerializer):
    center_info = LearningCenterShortSerializer(source='center', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Parent
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'phone_number', 'email',
            'address', 'workplace', 'relationship', 'center', 'center_info',
            'created_by', 'created_by_info', 'student_count', 'is_active'
        ]
        read_only_fields = ['created_by', 'full_name', 'student_count']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_student_count(self, obj):
        return Student.objects.filter(parent=obj, is_active=True).count()
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
            if request.user.role == 'admin' and not validated_data.get('center'):
                validated_data['center'] = request.user.center
        
        return super().create(validated_data)
    
    def validate_phone_number(self, value):
        """Telefon raqamni tekshirish"""
        if not value.startswith('+') and not value.isdigit():
            raise serializers.ValidationError("Telefon raqam noto'g'ri formatda")
        return value


class StudentSerializer(serializers.ModelSerializer):
    teacher_info = serializers.SerializerMethodField()
    center_info = LearningCenterShortSerializer(source='center', read_only=True)
    parent_info = ParentShortSerializer(source='parent', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    average_grade = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    homework_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'age', 'phone_number',
            'address', 'subject', 'teacher', 'teacher_info', 'center',
            'center_info', 'parent', 'parent_info', 'created_by', 'created_by_info',
            'average_grade', 'attendance_rate', 'homework_count', 'is_active'
        ]
        read_only_fields = ['created_by', 'full_name', 'average_grade', 
                           'attendance_rate', 'homework_count']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return UserInfoSerializer(obj.teacher).data
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_average_grade(self, obj):
        """Studentning o'rtacha bahosi"""
        grades = Grade.objects.filter(student=obj)
        if grades.exists():
            avg = grades.aggregate(avg_score=serializers.Avg('score'))['avg_score']
            return round(avg, 2) if avg else 0
        return 0
    
    def get_attendance_rate(self, obj):
        """Studentning davomat foizi (oxirgi 30 kun)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        attendances = Attendance.objects.filter(
            student=obj, 
            created_at__gte=thirty_days_ago
        )
        
        if attendances.exists():
            total_lessons = attendances.count() * 3  # Har kuni 3 dars
            attended_lessons = sum([
                1 for a in attendances 
                if a.lesson_1 or a.lesson_2 or a.lesson_3
            ])
            return round((attended_lessons / total_lessons) * 100, 2) if total_lessons > 0 else 0
        return 0
    
    def get_homework_count(self, obj):
        """Studentning uy vazifalari soni"""
        return Homework.objects.filter(students=obj, is_active=True).count()
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'teacher':
                data['teacher'] = request.user
                if not data.get('center'):
                    data['center'] = request.user.center
            
            # Yoshni tekshirish
            if 'age' in data and data['age'] < 5:
                raise serializers.ValidationError({
                    "age": "Yosh 5 dan katta bo'lishi kerak"
                })
        
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
    created_at_date = serializers.SerializerMethodField()
    created_at_time = serializers.SerializerMethodField()
    attendance_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_info', 'teacher', 'teacher_info',
            'lesson_1', 'lesson_2', 'lesson_3', 'created_at',
            'created_at_date', 'created_at_time', 'created_by', 
            'created_by_info', 'attendance_status'
        ]
        read_only_fields = ['created_at', 'created_by']
    
    def get_student_info(self, obj):
        if obj.student:
            return StudentShortSerializer(obj.student).data
        return None
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return UserInfoSerializer(obj.teacher).data
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_created_at_date(self, obj):
        return obj.created_at.date()
    
    def get_created_at_time(self, obj):
        return obj.created_at.time()
    
    def get_attendance_status(self, obj):
        """Davomat holatini aniqlash"""
        total_lessons = 3
        attended_lessons = sum([obj.lesson_1, obj.lesson_2, obj.lesson_3])
        
        if attended_lessons == total_lessons:
            return "full"
        elif attended_lessons > 0:
            return "partial"
        else:
            return "absent"
    
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
    grade_category = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_info', 'teacher', 'teacher_info',
            'subject', 'score', 'grade_category', 'comment', 'date', 
            'created_by', 'created_by_info'
        ]
        read_only_fields = ['teacher', 'created_by', 'grade_category']
    
    def get_student_info(self, obj):
        if obj.student:
            return StudentShortSerializer(obj.student).data
        return None
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return UserInfoSerializer(obj.teacher).data
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_grade_category(self, obj):
        """Bahoni kategoriyaga ajratish"""
        if obj.score >= 90:
            return "excellent"
        elif obj.score >= 80:
            return "good"
        elif obj.score >= 70:
            return "average"
        elif obj.score >= 60:
            return "below_average"
        else:
            return "poor"
    
    def validate_score(self, value):
        """Baho 1-100 oralig'ida bo'lishini tekshirish"""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Baho 1 dan 100 gacha bo'lishi kerak")
        return value
    
    def validate_date(self, value):
        """Sana kelajakda bo'lishini tekshirish"""
        if value > timezone.now().date():
            raise serializers.ValidationError("Sana kelajakda bo'lishi mumkin emas")
        return value
    
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
    payment_status = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'student', 'student_info', 'date', 'amount',
            'deadline', 'status', 'payment_status', 'days_overdue',
            'created_by', 'created_by_info'
        ]
        read_only_fields = ['created_by', 'payment_status', 'days_overdue']
    
    def get_student_info(self, obj):
        if obj.student:
            return StudentShortSerializer(obj.student).data
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_payment_status(self, obj):
        """To'lov holatini aniqlash"""
        today = timezone.now().date()
        
        if obj.status.lower() == 'paid':
            return 'paid'
        elif obj.deadline < today:
            return 'overdue'
        elif obj.deadline == today:
            return 'due_today'
        else:
            return 'pending'
    
    def get_days_overdue(self, obj):
        """Qancha kun o'tib qolgan"""
        today = timezone.now().date()
        if obj.deadline < today and obj.status.lower() != 'paid':
            return (today - obj.deadline).days
        return 0
    
    def validate_amount(self, value):
        """To'lov miqdori musbat bo'lishini tekshirish"""
        if value <= 0:
            raise serializers.ValidationError("To'lov miqdori musbat bo'lishi kerak")
        return value
    
    def validate(self, data):
        """Muddati to'lov sanasidan keyin bo'lishini tekshirish"""
        if data.get('deadline') and data.get('date'):
            if data['deadline'] < data['date']:
                raise serializers.ValidationError({
                    "deadline": "Muddat to'lov sanasidan oldin bo'lishi mumkin emas"
                })
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class NewsSerializer(serializers.ModelSerializer):
    center_info = LearningCenterShortSerializer(source='center', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    short_body = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'body', 'short_body', 'center', 'center_info',
            'created_by', 'created_by_info', 'created_at', 'created_at_formatted',
            'is_active'
        ]
        read_only_fields = ['created_at', 'created_by', 'short_body', 'created_at_formatted']
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_short_body(self, obj):
        """Yangilik matnini qisqartirish"""
        if len(obj.body) > 150:
            return obj.body[:150] + "..."
        return obj.body
    
    def get_created_at_formatted(self, obj):
        """Sana vaqtni formatlash"""
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
    
    def validate_title(self, value):
        """Sarlavhani tekshirish"""
        if len(value) < 5:
            raise serializers.ValidationError("Sarlavha juda qisqa")
        if len(value) > 255:
            raise serializers.ValidationError("Sarlavha juda uzun")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
            if request.user.role == 'admin' and not validated_data.get('center'):
                validated_data['center'] = request.user.center
        
        return super().create(validated_data)


# ========== Homework Serializers ==========

class HomeworkSerializer(serializers.ModelSerializer):
    teacher_info = serializers.SerializerMethodField()
    center_info = LearningCenterShortSerializer(source='center', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    students_info = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    is_due_today = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'title', 'description', 'due_date', 'homework_file',
            'teacher', 'teacher_info', 'students', 'students_info',
            'center', 'center_info', 'created_at', 'created_at_formatted',
            'created_by', 'created_by_info', 'is_active', 'student_count', 
            'file_url', 'file_name', 'file_size', 'days_remaining',
            'is_overdue', 'is_due_today', 'status'
        ]
        read_only_fields = ['created_at', 'created_by', 'teacher_info', 
                           'center_info', 'student_count', 'days_remaining',
                           'is_overdue', 'is_due_today', 'status', 
                           'created_at_formatted', 'file_name', 'file_size']
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return UserInfoSerializer(obj.teacher).data
        return None
    
    def get_center_info(self, obj):
        if obj.center:
            return LearningCenterShortSerializer(obj.center).data
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return UserInfoSerializer(obj.created_by).data
        return None
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def get_students_info(self, obj):
        """Uy vazifasi biriktirilgan o'quvchilar ma'lumotlari"""
        return StudentShortSerializer(obj.students.all(), many=True).data
    
    def get_file_url(self, obj):
        """Fayl URL'ini olish"""
        if obj.homework_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.homework_file.url)
            return obj.homework_file.url
        return None
    
    def get_file_name(self, obj):
        """Fayl nomini olish"""
        if obj.homework_file:
            return obj.homework_file.name.split('/')[-1]
        return None
    
    def get_file_size(self, obj):
        """Fayl hajmini olish"""
        if obj.homework_file:
            try:
                size = obj.homework_file.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
            except:
                return "Unknown"
        return None
    
    def get_created_at_formatted(self, obj):
        """Sana vaqtni formatlash"""
        return obj.created_at.strftime("%Y-%m-%d %H:%M")
    
    def get_days_remaining(self, obj):
        """Qolgan kunlar soni"""
        if obj.due_date:
            today = timezone.now().date()
            delta = (obj.due_date - today).days
            return max(0, delta) if delta > 0 else 0
        return None
    
    def get_is_overdue(self, obj):
        """Muddati o'tganmi?"""
        if obj.due_date:
            today = timezone.now().date()
            return today > obj.due_date
        return False
    
    def get_is_due_today(self, obj):
        """Bugun muddati kelganmi?"""
        if obj.due_date:
            today = timezone.now().date()
            return today == obj.due_date
        return False
    
    def get_status(self, obj):
        """Uy vazifasi holatini aniqlash"""
        if not obj.is_active:
            return "completed"
        
        if obj.due_date:
            today = timezone.now().date()
            if today > obj.due_date:
                return "overdue"
            elif today == obj.due_date:
                return "due_today"
            else:
                if obj.days_remaining <= 3:
                    return "urgent"
                else:
                    return "upcoming"
        
        return "active"
    
    def validate_title(self, value):
        """Sarlavhani tekshirish"""
        if len(value) < 3:
            raise serializers.ValidationError("Sarlavha juda qisqa")
        if len(value) > 255:
            raise serializers.ValidationError("Sarlavha juda uzun")
        return value
    
    def validate_description(self, value):
        """Tavsifni tekshirish"""
        if len(value) < 10:
            raise serializers.ValidationError("Tavsif juda qisqa")
        return value
    
    def validate_due_date(self, value):
        """Muddat bugundan oldin bo'lishini tekshirish"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Muddat bugungi sanadan oldin bo'lishi mumkin emas")
        return value
    
    def validate_homework_file(self, value):
        """Fayl hajmini tekshirish (max 10MB)"""
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("Fayl hajmi 10MB dan katta bo'lishi mumkin emas")
        
        # Ruxsat etilgan fayl formatlari
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.zip', '.rar']
        if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Faqat quyidagi formatlar qabul qilinadi: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def validate(self, data):
        """Teacher o'z markazidagi o'quvchilarga uy vazifasi berishi kerak"""
        request = self.context.get('request')
        
        if request and request.user.role == 'teacher':
            students = data.get('students', [])
            if students:
                for student in students:
                    if student.teacher != request.user:
                        raise serializers.ValidationError({
                            "students": f"{student.first_name} {student.last_name} - Bu o'quvchi sizga tegishli emas"
                        })
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # O'quvchilar ro'yxatini olish
        students = validated_data.pop('students', [])
        
        # Uy vazifasini yaratish
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            
            # Agar teacher o'rnatilmagan bo'lsa, o'zini teacher qilib o'rnatish
            if not validated_data.get('teacher') and request.user.role in ["teacher", "admin", "admin_mini"]:
                validated_data['teacher'] = request.user
            
            # Agar center o'rnatilmagan bo'lsa, teacher'ning center'ini olish
            if not validated_data.get('center') and request.user.center:
                validated_data['center'] = request.user.center
        
        homework = Homework.objects.create(**validated_data)
        
        # O'quvchilarni biriktirish
        if students:
            homework.students.set(students)
        
        return homework
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        
        # O'quvchilar ro'yxatini olish
        students = validated_data.pop('students', None)
        
        # Uy vazifasini yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # O'quvchilarni yangilash (agar berilgan bo'lsa)
        if students is not None:
            instance.students.set(students)
        
        return instance


class HomeworkListSerializer(serializers.ModelSerializer):
    """Uy vazifalari ro'yxati uchun qisqa serializer"""
    teacher_name = serializers.SerializerMethodField()
    center_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'title', 'teacher', 'teacher_name', 'center', 'center_name',
            'due_date', 'is_active', 'student_count', 'days_remaining', 
            'status', 'created_at', 'created_at_formatted'
        ]
        read_only_fields = fields
    
    def get_teacher_name(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return None
    
    def get_center_name(self, obj):
        if obj.center:
            return obj.center.name
        return None
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def get_days_remaining(self, obj):
        if obj.due_date:
            today = timezone.now().date()
            delta = (obj.due_date - today).days
            return max(0, delta)
        return None
    
    def get_status(self, obj):
        """Uy vazifasi holatini aniqlash"""
        if not obj.is_active:
            return "completed"
        
        if obj.due_date:
            today = timezone.now().date()
            if today > obj.due_date:
                return "overdue"
            elif today == obj.due_date:
                return "due_today"
            else:
                if self.get_days_remaining(obj) <= 3:
                    return "urgent"
                else:
                    return "upcoming"
        
        return "active"
    
    def get_created_at_formatted(self, obj):
        """Sana vaqtni formatlash"""
        return obj.created_at.strftime("%Y-%m-%d")


class StudentWithGradesSerializer(serializers.ModelSerializer):
    """Baholari bilan birga student serializer"""
    grades = serializers.SerializerMethodField()
    average_grade = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    homework_count = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'age', 'subject',
            'grades', 'average_grade', 'attendance_rate', 'homework_count', 'is_active'
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_grades(self, obj):
        """Studentning so'nggi 5 ta bahosi"""
        grades = Grade.objects.filter(student=obj).order_by('-date')[:5]
        return GradeSerializer(grades, many=True).data
    
    def get_average_grade(self, obj):
        """Studentning o'rtacha bahosi"""
        grades = Grade.objects.filter(student=obj)
        if grades.exists():
            avg = grades.aggregate(avg_score=serializers.Avg('score'))['avg_score']
            return round(avg, 2) if avg else 0
        return 0
    
    def get_attendance_rate(self, obj):
        """Studentning davomat foizi (oxirgi 30 kun)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        attendances = Attendance.objects.filter(
            student=obj, 
            created_at__gte=thirty_days_ago
        )
        
        if attendances.exists():
            total_lessons = attendances.count() * 3  # Har kuni 3 dars
            attended_lessons = sum([
                1 for a in attendances 
                if a.lesson_1 or a.lesson_2 or a.lesson_3
            ])
            return round((attended_lessons / total_lessons) * 100, 2) if total_lessons > 0 else 0
        return 0
    
    def get_homework_count(self, obj):
        """Studentning uy vazifalari soni"""
        return Homework.objects.filter(students=obj, is_active=True).count()


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistikasi uchun serializer"""
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    active_teachers = serializers.IntegerField()
    total_homeworks = serializers.IntegerField()
    active_homeworks = serializers.IntegerField()
    upcoming_homeworks = serializers.IntegerField()
    overdue_homeworks = serializers.IntegerField()
    total_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    total_news = serializers.IntegerField()
    total_grades = serializers.IntegerField()
    average_grade = serializers.FloatField()
    total_attendance = serializers.IntegerField()
    today_attendance = serializers.IntegerField()
    
    class Meta:
        fields = '__all__'


class StudentDetailSerializer(serializers.ModelSerializer):
    """Student detail ma'lumotlari uchun serializer"""
    teacher_info = serializers.SerializerMethodField()
    center_info = LearningCenterShortSerializer(source='center', read_only=True)
    parent_info = ParentShortSerializer(source='parent', read_only=True)
    full_name = serializers.SerializerMethodField()
    recent_grades = serializers.SerializerMethodField()
    recent_attendance = serializers.SerializerMethodField()
    recent_homeworks = serializers.SerializerMethodField()
    recent_payments = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'age', 'phone_number',
            'address', 'subject', 'teacher', 'teacher_info', 'center', 'center_info',
            'parent', 'parent_info', 'created_by', 'is_active',
            'recent_grades', 'recent_attendance', 'recent_homeworks',
            'recent_payments', 'statistics'
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_teacher_info(self, obj):
        if obj.teacher:
            return UserInfoSerializer(obj.teacher).data
        return None
    
    def get_recent_grades(self, obj):
        """Studentning so'nggi 10 ta bahosi"""
        grades = Grade.objects.filter(student=obj).order_by('-date')[:10]
        return GradeSerializer(grades, many=True).data
    
    def get_recent_attendance(self, obj):
        """Studentning so'nggi 10 ta davomati"""
        attendances = Attendance.objects.filter(student=obj).order_by('-created_at')[:10]
        return AttendanceSerializer(attendances, many=True).data
    
    def get_recent_homeworks(self, obj):
        """Studentning so'nggi 10 ta uy vazifasi"""
        homeworks = Homework.objects.filter(students=obj, is_active=True).order_by('-due_date')[:10]
        return HomeworkListSerializer(homeworks, many=True).data
    
    def get_recent_payments(self, obj):
        """Studentning so'nggi 10 ta to'lovi"""
        payments = Payment.objects.filter(student=obj).order_by('-date')[:10]
        return PaymentSerializer(payments, many=True).data
    
    def get_statistics(self, obj):
        """Student statistikasi"""
        # Baholar
        grades = Grade.objects.filter(student=obj)
        average_grade = 0
        if grades.exists():
            avg = grades.aggregate(avg_score=serializers.Avg('score'))['avg_score']
            average_grade = round(avg, 2) if avg else 0
        
        # Davomat
        thirty_days_ago = timezone.now() - timedelta(days=30)
        attendances = Attendance.objects.filter(
            student=obj, 
            created_at__gte=thirty_days_ago
        )
        attendance_rate = 0
        if attendances.exists():
            total_lessons = attendances.count() * 3
            attended_lessons = sum([
                1 for a in attendances 
                if a.lesson_1 or a.lesson_2 or a.lesson_3
            ])
            attendance_rate = round((attended_lessons / total_lessons) * 100, 2) if total_lessons > 0 else 0
        
        # Uy vazifalari
        total_homeworks = Homework.objects.filter(students=obj, is_active=True).count()
        completed_homeworks = Homework.objects.filter(students=obj, is_active=False).count()
        
        # To'lovlar
        payments = Payment.objects.filter(student=obj)
        total_payments = payments.count()
        paid_payments = payments.filter(status__icontains='paid').count()
        overdue_payments = payments.filter(status__icontains='overdue').count()
        
        return {
            'average_grade': average_grade,
            'attendance_rate': attendance_rate,
            'total_homeworks': total_homeworks,
            'completed_homeworks': completed_homeworks,
            'total_payments': total_payments,
            'paid_payments': paid_payments,
            'overdue_payments': overdue_payments 
        } 