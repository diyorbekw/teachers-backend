# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'learning-centers', views.LearningCenterViewSet)
router.register(r'parents', views.ParentViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'attendances', views.AttendanceViewSet)
router.register(r'grades', views.GradeViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'news', views.NewsViewSet)
router.register(r'homeworks', views.HomeworkViewSet)  # Homework uchun yangi endpoint

urlpatterns = [
    path('', include(router.urls)),
    
    # Custom endpoints
    path('dashboard/stats/', views.DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    path('students/<int:student_id>/grades/', views.StudentGradesAPIView.as_view(), name='student-grades'),
    path('students/<int:student_id>/attendance/', views.StudentAttendanceAPIView.as_view(), name='student-attendance'),
    path('students/<int:student_id>/payments/', views.StudentPaymentsAPIView.as_view(), name='student-payments'),
    
    # Teacher endpoints
    path('teacher/students/', views.TeacherStudentListAPIView.as_view(), name='teacher-students'),
    path('teacher/attendances/', views.TeacherAttendanceListAPIView.as_view(), name='teacher-attendances'),
    path('teacher/grades/', views.TeacherGradeListAPIView.as_view(), name='teacher-grades'),
    path('teacher/homeworks/', views.TeacherHomeworkListAPIView.as_view(), name='teacher-homeworks'),
    path('teacher/homeworks/<int:pk>/', views.TeacherHomeworkDetailAPIView.as_view(), name='teacher-homework-detail'),
]