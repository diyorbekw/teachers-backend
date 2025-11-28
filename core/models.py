# core/models.py
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator, EmailValidator

phone_validator = RegexValidator(r'^\+?\d{7,15}$', 'Telefon raqam noto\'g\'ri formatda')

class LearningCenter(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nomi")
    address = models.CharField(max_length=255, verbose_name="Manzil")
    phone_number = models.CharField(max_length=20, validators=[phone_validator], verbose_name="Telefon raqam")
    email = models.EmailField(validators=[EmailValidator()], verbose_name="Email")
    director = models.CharField(max_length=255, verbose_name="Direktor")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yaratgan admin")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "O'quv markaz"
        verbose_name_plural = "O'quv markazlar"

    def __str__(self):
        return self.name


class Parent(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    phone_number = models.CharField(max_length=20, validators=[phone_validator], verbose_name="Telefon raqam")
    email = models.EmailField(verbose_name="Email")
    address = models.CharField(max_length=255, verbose_name="Manzil")
    workplace = models.CharField(max_length=255, verbose_name="Ish joyi")
    relationship = models.CharField(max_length=50, verbose_name="Qarindoshlik")
    center = models.ForeignKey(LearningCenter, on_delete=models.CASCADE, verbose_name="O'quv markaz")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_parents', verbose_name="Yaratgan admin")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Ota-ona"
        verbose_name_plural = "Ota-onalar"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    age = models.PositiveIntegerField(verbose_name="Yosh")
    phone_number = models.CharField(max_length=20, validators=[phone_validator], verbose_name="Telefon raqam")
    address = models.CharField(max_length=255, verbose_name="Manzil")
    subject = models.CharField(max_length=100, verbose_name="Fan")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="students", verbose_name="O'qituvchi")
    center = models.ForeignKey(LearningCenter, on_delete=models.CASCADE, related_name="students", verbose_name="O'quv markaz")
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ota-ona")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_students', verbose_name="Yaratgan admin")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="O'quvchi")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="O'qituvchi")
    lesson_1 = models.BooleanField(default=False, verbose_name="Dars 1")
    lesson_2 = models.BooleanField(default=False, verbose_name="Dars 2")
    lesson_3 = models.BooleanField(default=False, verbose_name="Dars 3")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_attendances', verbose_name="Yaratgan admin")

    class Meta:
        verbose_name = "Davomat"
        verbose_name_plural = "Davomatlar"

    def __str__(self):
        return f"{self.student} - {self.created_at.date()}"


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="O'quvchi")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="O'qituvchi")
    subject = models.CharField(max_length=100, verbose_name="Fan")
    score = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], verbose_name="Baho")
    comment = models.TextField(blank=True, verbose_name="Izoh")
    date = models.DateField(verbose_name="Sana")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_grades', verbose_name="Yaratgan admin")

    class Meta:
        verbose_name = "Baholash"
        verbose_name_plural = "Baholar"

    def __str__(self):
        return f"{self.student} - {self.score}"


class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="O'quvchi")
    date = models.DateField(verbose_name="Sana")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Miqdor")
    deadline = models.DateField(verbose_name="To'lov sanasi")
    status = models.CharField(max_length=50, verbose_name="To'lov holati")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yaratgan admin")

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self):
        return f"{self.student} - {self.amount}"


class News(models.Model):
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    body = models.TextField(verbose_name="Matn")
    center = models.ForeignKey(LearningCenter, on_delete=models.CASCADE, related_name="news", verbose_name="O'quv markaz")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yaratgan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Yangilik"
        verbose_name_plural = "Yangiliklar"

    def __str__(self):
        return self.title