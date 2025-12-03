# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearningCenterViewSet, ParentViewSet, StudentViewSet,
    AttendanceViewSet, GradeViewSet, PaymentViewSet, NewsViewSet
)

router = DefaultRouter()
router.register(r'learning-centers', LearningCenterViewSet, basename='learningcenter')
router.register(r'parents', ParentViewSet, basename='parent')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'attendances', AttendanceViewSet, basename='attendance')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = [
    path('', include(router.urls)),
]