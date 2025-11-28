# core/management/commands/create_weekly_attendance.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from core.models import Attendance, Student
from account.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Har bir o\'qituvchi uchun o\'quvchilariga haftalik davomat yaratadi'

    def add_arguments(self, parser):
        parser.add_argument(
            '--teacher-id',
            type=int,
            help='Ma\'lum bir o\'qituvchi IDsi (agar bitta o\'qituvchi uchun yaratish kerak bo\'lsa)',
        )
        parser.add_argument(
            '--center-id',
            type=int,
            help='Ma\'lum bir o\'quv markaz IDsi (agar bitta markaz uchun yaratish kerak bo\'lsa)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Agar allaqachon mavjud bo\'lsa ham yangi davomat yaratish',
        )

    def handle(self, *args, **options):
        teacher_id = options.get('teacher_id')
        center_id = options.get('center_id')
        force = options.get('force')
        
        try:
            # O'qituvchilarni filtrlash
            teachers_query = User.objects.filter(role="teacher", is_active=True)
            
            if teacher_id:
                teachers_query = teachers_query.filter(id=teacher_id)
                if not teachers_query.exists():
                    self.stdout.write(
                        self.style.ERROR(f"ID {teacher_id} bo\'lgan faol o\'qituvchi topilmadi")
                    )
                    return
            
            if center_id:
                teachers_query = teachers_query.filter(center_id=center_id)
            
            teachers = teachers_query
            
            if not teachers.exists():
                self.stdout.write(
                    self.style.WARNING("Hech qanday faol o\'qituvchi topilmadi")
                )
                return
            
            created_count = 0
            skipped_count = 0
            
            for teacher in teachers:
                # Har bir o'qituvchining o'quvchilarini olish
                students = Student.objects.filter(
                    Q(teacher=teacher) | Q(created_by=teacher),
                    is_active=True
                )
                
                if not students.exists():
                    self.stdout.write(
                        self.style.WARNING(f"O\'qituvchi {teacher.full_name} uchun o\'quvchilar topilmadi")
                    )
                    continue
                
                teacher_created_count = 0
                teacher_skipped_count = 0
                
                for student in students:
                    # Bu hafta uchun davomat allaqachon mavjudligini tekshirish
                    today = timezone.now().date()
                    
                    if not force:
                        existing_attendance = Attendance.objects.filter(
                            student=student,
                            teacher=teacher,
                            created_at__date=today
                        ).exists()
                        
                        if existing_attendance:
                            teacher_skipped_count += 1
                            skipped_count += 1
                            continue
                    
                    # Yangi davomat yaratish
                    Attendance.objects.create(
                        student=student,
                        teacher=teacher,
                        lesson_1=False,
                        lesson_2=False,
                        lesson_3=False,
                        created_by=teacher
                    )
                    teacher_created_count += 1
                    created_count += 1
                
                if teacher_created_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"O\'qituvchi {teacher.full_name} uchun {teacher_created_count} ta davomat yaratildi"
                        )
                    )
                
                if teacher_skipped_count > 0 and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f"O\'qituvchi {teacher.full_name} uchun {teacher_skipped_count} ta davomat allaqachon mavjud (o\'tkazib yuborildi)"
                        )
                    )
            
            # Natijalarni ko'rsatish
            self.stdout.write(
                self.style.SUCCESS(
                    f"Jami: {created_count} ta yangi davomat yaratildi"
                )
            )
            
            if skipped_count > 0 and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"{skipped_count} ta davomat allaqachon mavjud (o\'tkazib yuborildi)"
                    )
                )
            
            logger.info(f"Ruchnoy davomat yaratildi: {created_count} ta")
            
        except Exception as e:
            error_msg = f"Davomat yaratishda xatolik: {str(e)}"
            self.stdout.write(
                self.style.ERROR(error_msg)
            )
            logger.error(error_msg)