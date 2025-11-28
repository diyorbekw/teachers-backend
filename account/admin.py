# account/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User
from django.utils.translation import gettext_lazy as _
from django import forms
from django.db.models import Q
from core.models import LearningCenter


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Foydalanuvchi rolini cheklash
        if hasattr(self, 'current_user'):
            if self.current_user.role == "admin":
                # Admin faqat teacher rolini tanlashi mumkin
                self.fields['role'].choices = [("teacher", "Teacher")]
        
        # Agar role teacher bo'lsa, teacher maydonlarini ko'rsat
        if self.instance and self.instance.role == "teacher":
            self.fields['age'].required = True
            self.fields['pinfl'].required = True
            self.fields['subject'].required = True
            self.fields['teacher_email'].required = True
            self.fields['teacher_phone_number'].required = True
            self.fields['center'].required = True
        else:
            # Teacher bo'lmaganlar uchun bu maydonlar kerak emas
            self.fields['age'].required = False
            self.fields['pinfl'].required = False
            self.fields['subject'].required = False
            self.fields['teacher_email'].required = False
            self.fields['teacher_phone_number'].required = False
            self.fields['center'].required = False

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        center = cleaned_data.get('center')
        
        # Agar role teacher bo'lsa, center majburiy
        if role == 'teacher' and not center:
            raise forms.ValidationError("Teacher uchun o'quv markaz belgilanishi shart")
        
        return cleaned_data


class AdminUserAdmin(BaseUserAdmin):
    form = UserAdminForm
    
    # Asosiy fieldsets
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Custom fields'), {'fields': ('role', 'center')}),
        (_('Teacher info'), {'fields': ('age', 'pinfl', 'subject', 'teacher_email', 'teacher_phone_number')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Superadmin uchun add fieldsets
    superadmin_add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'role', 'center', 'password1', 'password2'),
        }),
    )

    # Admin uchun add fieldsets (faqat teacher)
    admin_add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'center', 'password1', 'password2'),
        }),
    )

    list_display = ('id', 'phone_number', 'first_name', 'last_name', 'role', 'center', 'subject', 'is_staff', 'is_active')
    list_filter = ('role', 'center', 'subject', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('phone_number', 'first_name', 'last_name', 'subject')
    ordering = ('id',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        # Agar admin bo'lsa va yangi user qo'shilayotgan bo'lsa
        if request.user.role == "admin" and not obj:
            # Role maydonini olib tashlaymiz, chunki faqat teacher bo'ladi
            for fieldset in fieldsets:
                if fieldset[0] == _('Custom fields'):
                    fieldset[1]['fields'] = ['center']  # Faqat center qoldiramiz
        
        # Agar admin bo'lsa, faqat teacher rolini ko'rsatish
        if request.user.role == "admin":
            # Teacher bo'lmaganlar uchun teacher maydonlarini olib tashlaymiz
            if not obj or obj.role != "teacher":
                fieldsets = [fieldset for fieldset in fieldsets if fieldset[0] != _('Teacher info')]
        
        return fieldsets

    def get_add_fieldsets(self, request):
        """Qo'shish formasi uchun fieldsets ni sozlash"""
        if request.user.role == "admin":
            return self.admin_add_fieldsets
        else:
            return self.superadmin_add_fieldsets

    def add_view(self, request, form_url='', extra_context=None):
        """Qo'shish sahifasi"""
        self.add_fieldsets = self.get_add_fieldsets(request)
        return super().add_view(request, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "center":
            if request.user.role == "admin":
                # Admin faqat o'z markazini tanlashi mumkin
                if request.user.center and request.user.center.id:
                    kwargs["queryset"] = LearningCenter.objects.filter(id=request.user.center.id)
                    kwargs["initial"] = request.user.center
                else:
                    # Agar admin center ga ega bo'lmasa, hech narsa ko'rsatma
                    kwargs["queryset"] = LearningCenter.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # 1. Faqat superadmin va admin User modelini ko'rishi mumkin
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        
        if request.user.role == "superadmin":
            return qs
        elif request.user.role == "admin":
            # Admin: faqat o'zi qo'shgan teacherlarni va superadmin qo'shgan teacherlarni ko'radi
            return qs.filter(
                Q(role="teacher") & 
                (Q(created_by=request.user) | Q(created_by__role="superadmin"))
            )
        return qs.none()

    # 2. Faqat superadmin va admin User modeliga kirish huquqiga ega
    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.role in ["superadmin", "admin"]

    # 3. Faqat superadmin va admin yangi user qo'shishi mumkin
    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        
        # Django permission larini qo'shish
        if request.user.is_superuser:
            return True
        
        if request.user.role == "superadmin":
            return True
        elif request.user.role == "admin":
            # Admin faqat teacher qo'sha oladi
            return True
        return False

    # 4. Faqat superadmin va admin user ma'lumotlarini o'zgartirishi mumkin
    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        # Django permission larini qo'shish
        if request.user.is_superuser:
            return True
        
        if request.user.role == "superadmin":
            return True
        elif request.user.role == "admin":
            # Admin faqat o'zi qo'shgan teacherlarni o'zgartira oladi
            if obj and obj.role == "teacher" and obj.created_by == request.user:
                return True
        return False

    # 5. Faqat superadmin user o'chirishi mumkin
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        # Django permission larini qo'shish
        if request.user.is_superuser:
            return True
        
        return request.user.role == "superadmin"

    # 6. Faqat superadmin va admin user ma'lumotlarini ko'rishi mumkin
    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        
        # Django permission larini qo'shish
        if request.user.is_superuser:
            return True
        
        return request.user.role in ["superadmin", "admin"]

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            obj.created_by = request.user
            # Agar admin yangi user qo'shayotgan bo'lsa, avtomatik teacher qilamiz
            if request.user.role == "admin":
                obj.role = "teacher"
            # Agar admin teacher qo'shayotgan bo'lsa, markazni avtomatik o'rnatish
            if request.user.role == "admin" and not obj.center and request.user.center:
                obj.center = request.user.center
        super().save_model(request, obj, form, change)


# User modelini ro'yxatdan o'tkazish
admin.site.register(User, AdminUserAdmin)

# Group modelini admin dan olib tashlash
admin.site.unregister(Group)