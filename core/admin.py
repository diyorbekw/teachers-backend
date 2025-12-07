from django.contrib import admin
from django import forms
from django.urls import path
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from django.contrib import messages
from .models import Attendance, Student, Grade, Payment, News, LearningCenter, Parent, Homework
from account.models import User


# --- LearningCenter ---
@admin.register(LearningCenter)
class LearningCenterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone_number", "director", "created_by", "is_active")
    search_fields = ("name", "director")
    readonly_fields = ("created_by",)
    list_filter = ("is_active",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        u = request.user
        if u.role == "superadmin":
            return qs
        if u.role == "admin":
            return qs
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin":
            return True
        return False

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role == "superadmin"

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin" and obj:
            return obj.created_by == u
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == "superadmin"

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["superadmin", "admin"]

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# --- Parent ---
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "phone_number", "center", "created_by", "is_active")
    search_fields = ("first_name", "last_name", "phone_number")
    readonly_fields = ("created_by",)
    list_filter = ("center", "is_active")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_authenticated:
            if db_field.name == "center":
                kwargs["queryset"] = LearningCenter.objects.none()
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        if db_field.name == "center":
            if request.user.role == "superadmin":
                kwargs["queryset"] = LearningCenter.objects.all()
            elif request.user.role == "admin":
                # Admin: superadmin qo'shgan markazlar + o'z markazi
                kwargs["queryset"] = LearningCenter.objects.filter(
                    Q(created_by__role="superadmin") | Q(id=request.user.center.id)
                )
            else:
                kwargs["queryset"] = LearningCenter.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        u = request.user
        if u.role == "superadmin":
            return qs
        if u.role == "admin":
            return qs.filter(created_by__role="superadmin") | qs.filter(created_by=u)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin":
            if obj:
                return obj.created_by.role == "superadmin" or obj.created_by == u
            return True
        return False

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin"]

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin" and obj and obj.created_by == u:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin" and obj and obj.created_by == u:
            return True
        return False

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["superadmin", "admin"]

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated and request.user.role == "admin":
            obj.created_by = request.user
            if not obj.center:
                obj.center = request.user.center
        super().save_model(request, obj, form, change)


# --- Student ---
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "subject", "teacher", "center", "created_by", "is_active")
    search_fields = ("first_name", "last_name", "phone_number")
    list_filter = ("center", "subject", "teacher", "is_active")
    readonly_fields = ("created_by",)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_authenticated:
            if db_field.name in ["teacher", "center", "parent"]:
                kwargs["queryset"] = User.objects.none()
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        if db_field.name == "teacher":
            if request.user.role == "superadmin":
                kwargs["queryset"] = User.objects.filter(role="teacher")
            elif request.user.role == "admin":
                # Admin: superadmin qo'shgan teacherlar + o'z markazidagi teacherlar
                kwargs["queryset"] = User.objects.filter(
                    role="teacher",
                ).filter(
                    Q(created_by__role="superadmin") | Q(center=request.user.center)
                )
            elif request.user.role == "teacher":
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
            else:
                kwargs["queryset"] = User.objects.none()
        
        if db_field.name == "center":
            if request.user.role == "superadmin":
                kwargs["queryset"] = LearningCenter.objects.all()
            elif request.user.role == "admin":
                # Admin: superadmin qo'shgan markazlar + o'z markazi
                kwargs["queryset"] = LearningCenter.objects.filter(
                    Q(created_by__role="superadmin") | Q(id=request.user.center.id)
                )
            elif request.user.role == "teacher":
                if request.user.center:
                    kwargs["queryset"] = LearningCenter.objects.filter(id=request.user.center.id)
                else:
                    kwargs["queryset"] = LearningCenter.objects.none()
            else:
                kwargs["queryset"] = LearningCenter.objects.none()
        
        if db_field.name == "parent":
            if request.user.role == "superadmin":
                kwargs["queryset"] = Parent.objects.all()
            elif request.user.role == "admin":
                # Admin: superadmin qo'shgan ota-onalar + o'zi qo'shgan ota-onalar
                kwargs["queryset"] = Parent.objects.filter(
                    Q(created_by__role="superadmin") | Q(created_by=request.user)
                )
            elif request.user.role == "teacher":
                if request.user.center:
                    kwargs["queryset"] = Parent.objects.filter(center=request.user.center)
                else:
                    kwargs["queryset"] = Parent.objects.none()
            else:
                kwargs["queryset"] = Parent.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        u = request.user
        if u.role == "superadmin":
            return qs
        elif u.role in ["admin", "admin_mini"]:
            # Admin: superadmin qo'shganlar + o'zi qo'shganlar + o'z markazidagilar
            return qs.filter(
                Q(created_by__role="superadmin") | 
                Q(created_by=u) |
                Q(center=u.center)
            )
        elif u.role == "teacher":
            return qs.filter(teacher=u)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        elif u.role in ["admin", "admin_mini"]:
            if obj:
                return (obj.created_by.role == "superadmin" or 
                       obj.created_by == u or 
                       obj.center == u.center)
            return True
        elif u.role == "teacher":
            if obj:
                return obj.teacher == u
            return True
        return False

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin", "teacher"]

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        elif u.role in ["admin", "admin_mini"] and obj and (obj.created_by == u or obj.center == u.center):
            return True
        elif u.role == "teacher" and obj and obj.teacher == u:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin" and obj and obj.created_by == u:
            return True
        return False

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["superadmin", "admin", "teacher"]

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            if request.user.role == "teacher":
                obj.teacher = request.user
                obj.center = request.user.center
                obj.created_by = request.user
            elif request.user.role == "admin":
                obj.created_by = request.user
                if not obj.center:
                    obj.center = request.user.center
        super().save_model(request, obj, form, change)


# --- Attendance ---
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student', 
        'teacher', 
        'created_at_date',
        'lesson_1',
        'lesson_2', 
        'lesson_3',
    )
    
    list_editable = ('lesson_1', 'lesson_2', 'lesson_3')
    
    list_filter = ('teacher', 'created_at', 'student__center')
    search_fields = ('student__first_name', 'student__last_name', 'teacher__first_name', 'teacher__last_name')
    
    readonly_fields = ('created_at', 'created_by')
    
    actions = ['delete_selected_attendance']
    
    def created_at_date(self, obj):
        return obj.created_at.date()
    created_at_date.short_description = "Sana"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        user = request.user
        if hasattr(user, 'role'):
            if user.role == "superadmin":
                return qs
            elif user.role in ["admin", "admin_mini"]:
                # Admin: o'z markazidagi barcha davomatlar + superadmin qo'shganlar
                return qs.filter(
                    Q(student__center=user.center) |
                    Q(created_by__role="superadmin")
                )
            elif user.role == "teacher":
                return qs.filter(teacher=user)
        return qs.none()

    def has_module_permission(self, request):
        """App ni admin panelda ko'rish uchun ruxsat"""
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        return request.user.role in ["superadmin", "admin", "admin_mini", "teacher"]

    def has_view_permission(self, request, obj=None):
        """Ro'yxatni ko'rish uchun ruxsat"""
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        return request.user.role in ["superadmin", "admin", "admin_mini", "teacher"]

    def has_add_permission(self, request):
        """Yangi qo'shish uchun ruxsat"""
        return False  # Faqat avtomatik yoki command orqali qo'shilsin

    def has_change_permission(self, request, obj=None):
        """O'zgartirish uchun ruxsat"""
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"]:
            return True
        elif user.role == "teacher":
            # Teacher faqat o'zining davomatlarini o'zgartira oladi
            if obj:
                return obj.teacher == user
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """O'chirish uchun ruxsat"""
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"]:
            # Admin faqat o'zi yaratgan davomatlarni o'chira oladi
            if obj:
                return obj.created_by == user
            return True
        elif user.role == "teacher":
            # Teacher faqat o'zining davomatlarini o'chira oladi
            if obj:
                return obj.teacher == user
            return True
        return False

    def delete_selected_attendance(self, request, queryset):
        """Tanlangan davomatlarni o'chirish"""
        # Ruxsatni tekshirish
        for obj in queryset:
            if not self.has_delete_permission(request, obj):
                self.message_user(
                    request,
                    f"Siz {obj} ni o'chirish huquqiga ega emassiz",
                    messages.ERROR
                )
                return
        
        # O'chirish
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f"{count} ta davomat muvaffaqiyatli o'chirildi",
            messages.SUCCESS
        )
    
    delete_selected_attendance.short_description = "Tanlangan davomatlarni o'chirish"

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_actions(self, request):
        actions = super().get_actions(request)
        
        # Agar o'chirish ruxsati bo'lmasa, action ni olib tashlash
        if not self.has_delete_permission(request):
            if 'delete_selected_attendance' in actions:
                del actions['delete_selected_attendance']
            if 'delete_selected' in actions:
                del actions['delete_selected']
        
        return actions


# --- Grade Form va Admin ---
class GradeAdminForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'score', 'comment', 'date']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Foydalanuvchiga qarab studentlarni filtrlash
        if 'student' in self.fields:
            user = getattr(self, 'current_user', None)
            if user and hasattr(user, 'role'):
                if user.role == "teacher":
                    self.fields['student'].queryset = Student.objects.filter(
                        teacher=user, is_active=True
                    )
                elif user.role in ["admin", "admin_mini"]:
                    # Admin: o'z markazidagi barcha o'quvchilar + superadmin qo'shganlar
                    self.fields['student'].queryset = Student.objects.filter(
                        Q(center=user.center) | Q(created_by__role="superadmin"),
                        is_active=True
                    )

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    form = GradeAdminForm
    list_display = ("id", "student", "teacher", "subject", "score", "date", "created_by")
    readonly_fields = ("created_by", "teacher")
    list_filter = ("subject", "date", "student__center")
    search_fields = ("student__first_name", "student__last_name", "subject")
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        user = request.user
        if hasattr(user, 'role'):
            if user.role == "superadmin":
                return qs
            elif user.role in ["admin", "admin_mini"]:
                # Admin: o'z markazidagi barcha baholar + superadmin qo'shganlar
                return qs.filter(
                    Q(student__center=user.center) |
                    Q(created_by__role="superadmin")
                )
            elif user.role == "teacher":
                return qs.filter(teacher=user)
        return qs.none()

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        return request.user.role in ["superadmin", "admin", "admin_mini", "teacher"]

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"]:
            if obj:
                return obj.student.center == user.center or obj.created_by.role == "superadmin"
            return True
        elif user.role == "teacher":
            if obj:
                return obj.teacher == user
            return True
        return False

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin", "teacher"]

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"] and obj and obj.created_by == user:
            return True
        elif user.role == "teacher" and obj and obj.teacher == user:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"] and obj and obj.created_by == user:
            return True
        elif user.role == "teacher" and obj and obj.teacher == user:
            return True
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            # Yangi baho qo'shilganda teacher ni avtomatik o'rnatish
            obj.teacher = request.user
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# --- Payment ---
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "amount", "date", "deadline", "status", "created_by")
    search_fields = ("student__first_name", "student__last_name", "status")
    readonly_fields = ("created_by",)
    list_filter = ("status", "date", "deadline")
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_authenticated:
            if db_field.name == "student":
                kwargs["queryset"] = Student.objects.none()
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        if db_field.name == "student":
            if request.user.role == "superadmin":
                kwargs["queryset"] = Student.objects.all()
            elif request.user.role in ["admin", "admin_mini"]:
                # Admin: superadmin qo'shgan o'quvchilar + o'zi qo'shganlar + o'z markazidagilar
                kwargs["queryset"] = Student.objects.filter(
                    Q(created_by__role="superadmin") | 
                    Q(created_by=request.user) |
                    Q(center=request.user.center)
                )
            else:
                kwargs["queryset"] = Student.objects.none()
                
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        u = request.user
        if u.role == "superadmin":
            return qs
        if u.role in ["admin", "admin_mini"]:
            return qs.filter(
                Q(created_by__role="superadmin") | 
                Q(created_by=u) |
                Q(student__center=u.center)
            )
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role in ["admin", "admin_mini"]:
            if obj:
                return (obj.created_by.role == "superadmin" or 
                       obj.created_by == u or 
                       obj.student.center == u.center)
            return True
        return False

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin", "admin_mini"]

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role in ["admin", "admin_mini"] and obj and obj.created_by == u:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role in ["admin", "admin_mini"] and obj and obj.created_by == u:
            return True
        return False

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["superadmin", "admin", "admin_mini"]

    def save_model(self, request, obj, form, change):
        if not obj.created_by and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# --- News ---
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "center", "created_by", "created_at", "is_active")
    search_fields = ("title", "body")
    readonly_fields = ("created_at", "created_by")
    list_filter = ("center", "is_active", "created_at")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_authenticated:
            if db_field.name == "center":
                kwargs["queryset"] = LearningCenter.objects.none()
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        if db_field.name == "center":
            if request.user.role == "superadmin":
                kwargs["queryset"] = LearningCenter.objects.all()
            elif request.user.role == "admin":
                # Admin: superadmin qo'shgan markazlar + o'z markazi
                kwargs["queryset"] = LearningCenter.objects.filter(
                    Q(created_by__role="superadmin") | Q(id=request.user.center.id)
                )
            else:
                kwargs["queryset"] = LearningCenter.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        u = request.user
        if u.role == "superadmin":
            return qs
        if u.role == "admin":
            return qs.filter(created_by__role="superadmin") | qs.filter(created_by=u)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin":
            if obj:
                return obj.created_by.role == "superadmin" or obj.created_by == u
            return True
        return False

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin"]

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin" and obj and obj.created_by == u:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        u = request.user
        if u.role == "superadmin":
            return True
        if u.role == "admin" and obj and obj.created_by == u:
            return True
        return False

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["superadmin", "admin"]

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            if request.user.role == "admin":
                obj.center = request.user.center
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# --- Homework Form va Admin ---
class HomeworkAdminForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['title', 'description', 'due_date', 'homework_file', 'teacher', 'students', 'center', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Foydalanuvchiga qarab queryserlarni filtratsiya qilish
        if 'teacher' in self.fields:
            user = getattr(self, 'current_user', None)
            if user and hasattr(user, 'role'):
                if user.role == "superadmin":
                    self.fields['teacher'].queryset = User.objects.filter(role__in=["teacher", "admin", "admin_mini"])
                elif user.role == "admin":
                    # Admin: superadmin qo'shgan teacherlar + o'z markazidagi teacherlar
                    self.fields['teacher'].queryset = User.objects.filter(
                        Q(role__in=["teacher", "admin_mini"]) &
                        (Q(created_by__role="superadmin") | Q(center=user.center))
                    )
                elif user.role == "teacher":
                    self.fields['teacher'].queryset = User.objects.filter(id=user.id)
                    self.fields['teacher'].initial = user
                else:
                    self.fields['teacher'].queryset = User.objects.none()
        
        if 'students' in self.fields:
            user = getattr(self, 'current_user', None)
            if user and hasattr(user, 'role'):
                if user.role == "superadmin":
                    self.fields['students'].queryset = Student.objects.filter(is_active=True)
                elif user.role in ["admin", "admin_mini"]:
                    # Admin: superadmin qo'shgan o'quvchilar + o'zi qo'shganlar + o'z markazidagilar
                    self.fields['students'].queryset = Student.objects.filter(
                        (Q(created_by__role="superadmin") | 
                         Q(created_by=user) |
                         Q(center=user.center)) &
                        Q(is_active=True)
                    )
                elif user.role == "teacher":
                    self.fields['students'].queryset = Student.objects.filter(
                        teacher=user,
                        is_active=True
                    )
                else:
                    self.fields['students'].queryset = Student.objects.none()
        
        if 'center' in self.fields:
            user = getattr(self, 'current_user', None)
            if user and hasattr(user, 'role'):
                if user.role == "superadmin":
                    self.fields['center'].queryset = LearningCenter.objects.all()
                elif user.role in ["admin", "admin_mini", "teacher"]:
                    if user.center:
                        self.fields['center'].queryset = LearningCenter.objects.filter(id=user.center.id)
                        self.fields['center'].initial = user.center
                    else:
                        self.fields['center'].queryset = LearningCenter.objects.none()
                else:
                    self.fields['center'].queryset = LearningCenter.objects.none()

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    form = HomeworkAdminForm
    list_display = (
        'id',
        'title',
        'teacher_display',
        'student_count',
        'center_display',
        'due_date',
        'is_active_display',
        'created_at',
    )
    
    list_filter = (
        'center',
        'teacher',
        'due_date',
        'is_active',
        'created_at',
    )
    
    search_fields = (
        'title',
        'description',
        'teacher__first_name',
        'teacher__last_name',
    )
    
    readonly_fields = (
        'created_at',
        'created_by',
    )
    
    filter_horizontal = ('students',)
    
    fieldsets = (
        ('Asosiy maʼlumotlar', {
            'fields': ('title', 'description', 'due_date', 'homework_file')
        }),
        ('Biriktirishlar', {
            'fields': ('teacher', 'students', 'center')
        }),
        ('Qoʻshimcha maʼlumotlar', {
            'fields': ('is_active', 'created_at', 'created_by')
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_inactive', 'assign_to_all_students']
    
    def teacher_display(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return "Biriktirilmagan"
    teacher_display.short_description = "O'qituvchi"
    
    def center_display(self, obj):
        if obj.center:
            return obj.center.name
        return "Markaz biriktirilmagan"
    center_display.short_description = "O'quv markaz"
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "O'quvchilar soni"
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Faol</span>')
        else:
            return format_html('<span style="color: red;">✗ Nofaol</span>')
    is_active_display.short_description = "Holati"
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        user = request.user
        if hasattr(user, 'role'):
            if user.role == "superadmin":
                return qs
            elif user.role in ["admin", "admin_mini"]:
                # Admin: superadmin qo'shganlar + o'zi qo'shganlar + o'z markazidagilar
                return qs.filter(
                    Q(created_by__role="superadmin") | 
                    Q(created_by=user) |
                    Q(center=user.center)
                )
            elif user.role == "teacher":
                return qs.filter(teacher=user)
        return qs.none()
    
    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        return request.user.role in ["superadmin", "admin", "admin_mini", "teacher"]
    
    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"]:
            if obj:
                return (obj.created_by.role == "superadmin" or 
                       obj.created_by == user or 
                       obj.center == user.center)
            return True
        elif user.role == "teacher":
            if obj:
                return obj.teacher == user
            return True
        return False
    
    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin", "admin_mini", "teacher"]
    
    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"]:
            if obj and obj.created_by == user:
                return True
        elif user.role == "teacher":
            if obj and obj.teacher == user:
                return True
        return False
    
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'role'):
            return request.user.is_superuser
        
        user = request.user
        if user.role == "superadmin":
            return True
        elif user.role in ["admin", "admin_mini"]:
            if obj and obj.created_by == user:
                return True
        elif user.role == "teacher":
            if obj and obj.teacher == user:
                return True
        return False
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            
            # Agar teacher o'rnatilmagan bo'lsa, request.user ni teacher sifatida o'rnatish
            if not obj.teacher and request.user.role in ["teacher", "admin", "admin_mini"]:
                obj.teacher = request.user
            
            # Agar center o'rnatilmagan bo'lsa, teacher'ning center'ini olish
            if not obj.center and obj.teacher and obj.teacher.center:
                obj.center = obj.teacher.center
            elif not obj.center and request.user.center:
                obj.center = request.user.center
        
        super().save_model(request, obj, form, change)
    
    # Custom actions
    def mark_as_completed(self, request, queryset):
        """Tanlangan uy vazifalarini bajarilgan deb belgilash"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} ta uy vazifasi bajarilgan deb belgilandi",
            messages.SUCCESS
        )
    mark_as_completed.short_description = "Bajarilgan deb belgilash"
    
    def mark_as_inactive(self, request, queryset):
        """Tanlangan uy vazifalarini nofaol qilish"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} ta uy vazifasi nofaol qilindi",
            messages.SUCCESS
        )
    mark_as_inactive.short_description = "Nofaol qilish"
    
    def assign_to_all_students(self, request, queryset):
        """Tanlangan uy vazifalarini barcha o'quvchilarga biriktirish"""
        user = request.user
        
        for homework in queryset:
            if user.role == "superadmin":
                students = Student.objects.filter(is_active=True)
            elif user.role in ["admin", "admin_mini"]:
                students = Student.objects.filter(
                    center=user.center,
                    is_active=True
                )
            elif user.role == "teacher":
                students = Student.objects.filter(
                    teacher=user,
                    is_active=True
                )
            else:
                continue
            
            homework.students.add(*students)
        
        self.message_user(
            request,
            f"{queryset.count()} ta uy vazifasi barcha o'quvchilarga biriktirildi",
            messages.SUCCESS
        )
    assign_to_all_students.short_description = "Barcha o'quvchilarga biriktirish"
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        
        # Agar o'chirish ruxsati bo'lmasa, delete action'ni olib tashlash
        if not self.has_delete_permission(request):
            if 'delete_selected' in actions:
                del actions['delete_selected']
        
        return actions
    
    # Change list uchun qo'shimcha funksiyalar
    def changelist_view(self, request, extra_context=None):
        # Qo'shimcha kontekst ma'lumotlari
        extra_context = extra_context or {}
        
        user = request.user
        if hasattr(user, 'role'):
            if user.role == "teacher":
                # Teacher uchun statistikalar
                active_homeworks = self.get_queryset(request).filter(is_active=True).count()
                total_students = Student.objects.filter(teacher=user, is_active=True).count()
                
                extra_context.update({
                    'active_homeworks': active_homeworks,
                    'total_students': total_students,
                })
        
        return super().changelist_view(request, extra_context=extra_context)