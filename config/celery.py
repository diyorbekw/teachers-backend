# config/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Davriy vazifalar
app.conf.beat_schedule = {
    'create-weekly-attendance': {
        'task': 'core.tasks.create_weekly_attendance',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),  # Har dushanba 00:00
    },
}

app.conf.timezone = 'Asia/Tashkent'