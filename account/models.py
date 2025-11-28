# account/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

phone_validator = RegexValidator(r'^\+?\d{7,15}$', 'Telefon raqam noto\'g\'ri formatda')

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "superadmin")
        extra_fields.setdefault("center", None)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ("superadmin", "Super Admin"),
        ("admin", "Admin"),
        ("admin_mini", "Admin Mini"),
        ("teacher", "Teacher"),
    )

    username = None
    email = None

    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Teacher ma'lumotlari (faqat teacher rolida bo'lsa)
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(80)], 
        verbose_name="Yosh",
        null=True, 
        blank=True
    )
    pinfl = models.CharField(max_length=14, verbose_name="PINFL", null=True, blank=True)
    subject = models.CharField(max_length=100, verbose_name="Fan", null=True, blank=True)
    teacher_email = models.EmailField(verbose_name="Email", null=True, blank=True)
    teacher_phone_number = models.CharField(
        max_length=20, 
        validators=[phone_validator], 
        verbose_name="Telefon raqam",
        null=True, 
        blank=True
    )

    # center — barcha admin/admin_mini/teacher lar uchun mavjud
    center = models.ForeignKey(
        "core.LearningCenter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users"
    )

    # Yangi qo'shilgan maydon
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
        verbose_name="Yaratgan foydalanuvchi"
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.phone_number} - {self.role}"

    @property
    def is_teacher(self):
        return self.role == "teacher"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        # Agar user teacher bo'lmasa, teacher ma'lumotlarini null qilamiz
        if self.role != "teacher":
            self.age = None
            self.pinfl = None
            self.subject = None
            self.teacher_email = None
            self.teacher_phone_number = None
        
        super().save(*args, **kwargs)