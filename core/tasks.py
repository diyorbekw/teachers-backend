# core/tasks.py
from django.utils import timezone
from django.db.models import Q
from celery import shared_task
from .models import Attendance, Student, User
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_weekly_attendance():
    """
    Har hafta dushanba kuni 00:00da har bir o'qituvchi uchun 
    o'quvchilariga davomat yaratadi
    """
    try:
        # Faqat teacher rolidagi foydalanuvchilarni olish
        teachers = User.objects.filter(role="teacher", is_active=True)
        
        created_count = 0
        
        for teacher in teachers:
            # Har bir o'qituvchining o'quvchilarini olish
            students = Student.objects.filter(
                Q(teacher=teacher) | Q(created_by=teacher),
                is_active=True
            )
            
            for student in students:
                # Bu hafta uchun davomat allaqachon mavjudligini tekshirish
                today = timezone.now().date()
                existing_attendance = Attendance.objects.filter(
                    student=student,
                    teacher=teacher,
                    created_at__date=today
                ).exists()
                
                if not existing_attendance:
                    # Yangi davomat yaratish
                    Attendance.objects.create(
                        student=student,
                        teacher=teacher,
                        lesson_1=False,
                        lesson_2=False,
                        lesson_3=False,
                        created_by=teacher
                    )
                    created_count += 1
        
        logger.info(f"Avtomatik davomat yaratildi: {created_count} ta")
        return f"Yaratilgan davomatlar: {created_count} ta"
        
    except Exception as e:
        logger.error(f"Davomat yaratishda xatolik: {str(e)}")
        return f"Xatolik: {str(e)}"