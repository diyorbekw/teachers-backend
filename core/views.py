# core/views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    LearningCenter, Parent, Student, 
    Attendance, Grade, Payment, News, Homework
)
from .serializers import (
    LearningCenterSerializer, ParentSerializer,
    StudentSerializer, AttendanceSerializer,
    GradeSerializer, PaymentSerializer, 
    NewsSerializer, HomeworkSerializer
)


# ========== LearningCenterViewSet ==========
class LearningCenterViewSet(viewsets.ModelViewSet):
    queryset = LearningCenter.objects.all()
    serializer_class = LearningCenterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'address', 'director', 'phone_number']
    ordering_fields = ['id', 'name']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return LearningCenter.objects.filter(is_active=True)
        
        if user.role == "superadmin":
            return LearningCenter.objects.all()
        
        elif user.role == "admin":
            return LearningCenter.objects.filter(
                Q(created_by__role="superadmin") | Q(id=user.center.id)
            )
        
        elif user.role in ["admin_mini", "teacher"]:
            if user.center:
                return LearningCenter.objects.filter(id=user.center.id)
            return LearningCenter.objects.none()
        
        return LearningCenter.objects.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        if request.user.role != "superadmin":
            return Response(
                {"detail": "Only superadmin can create learning centers."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only update centers created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only update centers created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if request.user.role != "superadmin":
            return Response(
                {"detail": "Only superadmin can delete learning centers."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== ParentViewSet ==========
class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['center', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_number', 'email', 'workplace']
    ordering_fields = ['id', 'first_name', 'last_name']
    ordering = ['last_name', 'first_name']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Parent.objects.filter(is_active=True)
        
        if user.role == "superadmin":
            return Parent.objects.all()
        
        elif user.role == "admin":
            return Parent.objects.filter(
                Q(created_by__role="superadmin") | Q(created_by=user)
            )
        
        elif user.role in ["admin_mini", "teacher"]:
            if user.center:
                return Parent.objects.filter(center=user.center, is_active=True)
            return Parent.objects.none()
        
        return Parent.objects.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        if request.user.role not in ["superadmin", "admin"]:
            return Response(
                {"detail": "You do not have permission to create parents."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only update parents created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only update parents created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only delete parents created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== StudentViewSet ==========
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['center', 'teacher', 'subject', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_number', 'address', 'subject']
    ordering_fields = ['id', 'first_name', 'last_name', 'age']
    ordering = ['last_name', 'first_name']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Student.objects.filter(is_active=True)
        
        if user.role == "superadmin":
            return Student.objects.all()
        
        elif user.role in ["admin", "admin_mini"]:
            return Student.objects.filter(
                Q(created_by__role="superadmin") | 
                Q(created_by=user) |
                Q(center=user.center)
            )
        
        elif user.role == "teacher":
            return Student.objects.filter(teacher=user, is_active=True)
        
        return Student.objects.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        if request.user.role not in ["superadmin", "admin", "teacher"]:
            return Response(
                {"detail": "You do not have permission to create students."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"]:
            if instance.created_by != user and instance.center != user.center:
                return Response(
                    {"detail": "You can only update your own students or students in your center."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif user.role == "teacher":
            if instance.teacher != user:
                return Response(
                    {"detail": "You can only update your own students."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"]:
            if instance.created_by != user and instance.center != user.center:
                return Response(
                    {"detail": "You can only update your own students or students in your center."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif user.role == "teacher":
            if instance.teacher != user:
                return Response(
                    {"detail": "You can only update your own students."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only delete students created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_teacher(self, request):
        teacher_id = request.query_params.get('teacher_id')
        user = request.user
        
        if teacher_id:
            queryset = self.filter_queryset(
                self.get_queryset().filter(teacher_id=teacher_id, is_active=True)
            )
        elif user.role == "teacher":
            queryset = self.filter_queryset(
                self.get_queryset().filter(teacher=user, is_active=True)
            )
        else:
            return Response(
                {"detail": "teacher_id parameter is required for non-teacher users."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_center(self, request):
        center_id = request.query_params.get('center_id')
        user = request.user
        
        if center_id:
            queryset = self.filter_queryset(
                self.get_queryset().filter(center_id=center_id, is_active=True)
            )
        elif user.center:
            queryset = self.filter_queryset(
                self.get_queryset().filter(center=user.center, is_active=True)
            )
        else:
            return Response(
                {"detail": "center_id parameter is required or user must have a center."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== AttendanceViewSet ==========
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['teacher', 'lesson_1', 'lesson_2', 'lesson_3']
    search_fields = ['student__first_name', 'student__last_name', 'teacher__first_name', 'teacher__last_name']
    ordering_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Attendance.objects.none()
        
        if user.role == "superadmin":
            return Attendance.objects.all()
        
        elif user.role in ["admin", "admin_mini"]:
            return Attendance.objects.filter(
                Q(student__center=user.center) |
                Q(created_by__role="superadmin")
            )
        
        elif user.role == "teacher":
            return Attendance.objects.filter(teacher=user)
        
        return Attendance.objects.none()
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "teacher" and instance.teacher != user:
            return Response(
                {"detail": "You can only update your own attendance records."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "teacher" and instance.teacher != user:
            return Response(
                {"detail": "You can only update your own attendance records."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"]:
            if instance.created_by != user:
                return Response(
                    {"detail": "You can only delete attendance records created by you."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif user.role == "teacher":
            if instance.teacher != user:
                return Response(
                    {"detail": "You can only delete your own attendance records."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        queryset = self.filter_queryset(
            self.get_queryset().filter(created_at__date=today)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {"detail": "student_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(student_id=student_id)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== GradeViewSet ==========
class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['teacher', 'subject', 'date']
    search_fields = ['student__first_name', 'student__last_name', 'subject', 'comment']
    ordering_fields = ['id', 'date', 'score']
    ordering = ['-date']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Grade.objects.none()
        
        if user.role == "superadmin":
            return Grade.objects.all()
        
        elif user.role in ["admin", "admin_mini"]:
            return Grade.objects.filter(
                Q(student__center=user.center) |
                Q(created_by__role="superadmin")
            )
        
        elif user.role == "teacher":
            return Grade.objects.filter(teacher=user)
        
        return Grade.objects.none()
    
    def create(self, request, *args, **kwargs):
        if request.user.role not in ["superadmin", "admin", "teacher"]:
            return Response(
                {"detail": "You do not have permission to create grades."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"]:
            if instance.created_by != user:
                return Response(
                    {"detail": "You can only update grades created by you."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif user.role == "teacher":
            if instance.teacher != user:
                return Response(
                    {"detail": "You can only update your own grades."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"]:
            if instance.created_by != user:
                return Response(
                    {"detail": "You can only update grades created by you."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif user.role == "teacher":
            if instance.teacher != user:
                return Response(
                    {"detail": "You can only update your own grades."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"]:
            if instance.created_by != user:
                return Response(
                    {"detail": "You can only delete grades created by you."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        elif user.role == "teacher":
            if instance.teacher != user:
                return Response(
                    {"detail": "You can only delete your own grades."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {"detail": "student_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(student_id=student_id)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== PaymentViewSet ==========
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'student__center']
    search_fields = ['student__first_name', 'student__last_name', 'status']
    ordering_fields = ['id', 'date', 'deadline', 'amount']
    ordering = ['-date']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Payment.objects.none()
        
        if user.role == "superadmin":
            return Payment.objects.all()
        
        elif user.role in ["admin", "admin_mini"]:
            return Payment.objects.filter(
                Q(created_by__role="superadmin") | 
                Q(created_by=user) |
                Q(student__center=user.center)
            )
        
        return Payment.objects.none()
    
    def create(self, request, *args, **kwargs):
        if request.user.role not in ["superadmin", "admin", "admin_mini"]:
            return Response(
                {"detail": "You do not have permission to create payments."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"] and instance.created_by != user:
            return Response(
                {"detail": "You can only update payments created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"] and instance.created_by != user:
            return Response(
                {"detail": "You can only update payments created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"] and instance.created_by != user:
            return Response(
                {"detail": "You can only delete payments created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        today = timezone.now().date()
        queryset = self.filter_queryset(
            self.get_queryset().filter(deadline__lt=today, status__in=['pending', 'overdue'])
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {"detail": "student_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(student_id=student_id)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== NewsViewSet ==========
class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['center', 'is_active']
    search_fields = ['title', 'body']
    ordering_fields = ['id', 'created_at', 'title']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return News.objects.filter(is_active=True)
        
        if user.role == "superadmin":
            return News.objects.all()
        
        elif user.role == "admin":
            return News.objects.filter(
                Q(created_by__role="superadmin") | Q(created_by=user)
            )
        
        elif user.role in ["admin_mini", "teacher"]:
            if user.center:
                return News.objects.filter(center=user.center, is_active=True)
            return News.objects.none()
        
        return News.objects.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        if request.user.role not in ["superadmin", "admin"]:
            return Response(
                {"detail": "You do not have permission to create news."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only update news created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only update news created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin" and instance.created_by != user:
            return Response(
                {"detail": "You can only delete news created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== HomeworkViewSet ==========
class HomeworkViewSet(viewsets.ModelViewSet):
    """
    Uy vazifalari uchun ViewSet
    """
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['teacher', 'center', 'is_active', 'due_date']
    search_fields = ['title', 'description', 'teacher__first_name', 'teacher__last_name']
    ordering_fields = ['id', 'title', 'due_date', 'created_at']
    ordering = ['-due_date', '-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Homework.objects.none()
        
        if user.role == "superadmin":
            return Homework.objects.all()
        
        elif user.role in ["admin", "admin_mini"]:
            return Homework.objects.filter(
                Q(created_by=user) | Q(center=user.center)
            )
        
        elif user.role == "teacher":
            return Homework.objects.filter(teacher=user)
        
        return Homework.objects.none()
    
    def create(self, request, *args, **kwargs):
        if request.user.role not in ["superadmin", "admin", "admin_mini", "teacher"]:
            return Response(
                {"detail": "You do not have permission to create homeworks."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"] and instance.created_by != user:
            return Response(
                {"detail": "You can only update homeworks created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        elif user.role == "teacher" and instance.teacher != user:
            return Response(
                {"detail": "You can only update your own homeworks."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"] and instance.created_by != user:
            return Response(
                {"detail": "You can only update homeworks created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        elif user.role == "teacher" and instance.teacher != user:
            return Response(
                {"detail": "You can only update your own homeworks."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role in ["admin", "admin_mini"] and instance.created_by != user:
            return Response(
                {"detail": "You can only delete homeworks created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        elif user.role == "teacher" and instance.teacher != user:
            return Response(
                {"detail": "You can only delete your own homeworks."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = self.request.user
        homework = serializer.save(created_by=user)
        
        # Agar teacher o'rnatilmagan bo'lsa, o'zini teacher qilib o'rnatish
        if not homework.teacher and user.role in ["teacher", "admin", "admin_mini"]:
            homework.teacher = user
        
        # Agar center o'rnatilmagan bo'lsa, teacher'ning center'ini olish
        if not homework.center and user.center:
            homework.center = user.center
        
        homework.save()
    
    @action(detail=True, methods=['post'])
    def assign_students(self, request, pk=None):
        """Uy vazifasiga o'quvchilarni biriktirish"""
        homework = self.get_object()
        student_ids = request.data.get('student_ids', [])
        
        if not student_ids:
            return Response(
                {'error': 'student_ids maydoni majburiy'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # O'quvchilarni filtratsiya qilish
        user = request.user
        if user.role == "superadmin":
            students = Student.objects.filter(id__in=student_ids, is_active=True)
        elif user.role in ["admin", "admin_mini"]:
            students = Student.objects.filter(
                id__in=student_ids,
                center=user.center,
                is_active=True
            )
        elif user.role == "teacher":
            students = Student.objects.filter(
                id__in=student_ids,
                teacher=user,
                is_active=True
            )
        else:
            students = Student.objects.none()
        
        homework.students.add(*students)
        
        return Response({
            'message': f'{students.count()} ta o\'quvchi biriktirildi',
            'assigned_students': StudentSerializer(students, many=True).data
        })
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Uy vazifasiga biriktirilgan o'quvchilar ro'yxati"""
        homework = self.get_object()
        students = homework.students.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Faol uy vazifalari"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Kelgusi uy vazifalari"""
        today = timezone.now().date()
        queryset = self.filter_queryset(
            self.get_queryset().filter(due_date__gte=today, is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Muddati o'tgan uy vazifalari"""
        today = timezone.now().date()
        queryset = self.filter_queryset(
            self.get_queryset().filter(due_date__lt=today, is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_teacher(self, request):
        """Teacher'ning uy vazifalari"""
        teacher_id = request.query_params.get('teacher_id')
        user = request.user
        
        if teacher_id:
            queryset = self.filter_queryset(
                self.get_queryset().filter(teacher_id=teacher_id, is_active=True)
            )
        elif user.role == "teacher":
            queryset = self.filter_queryset(
                self.get_queryset().filter(teacher=user, is_active=True)
            )
        else:
            return Response(
                {"detail": "teacher_id parameter is required for non-teacher users."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """O'quvchining uy vazifalari"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {"detail": "student_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(students__id=student_id, is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== Custom API Views ==========

class TeacherHomeworkListAPIView(ListAPIView):
    """
    Teacher uchun uy vazifalari ro'yxati
    """
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role != "teacher":
            return Homework.objects.none()
        
        queryset = Homework.objects.filter(teacher=user)
        
        # Filtrlash parametrlari
        is_active = self.request.query_params.get('is_active')
        due_date = self.request.query_params.get('due_date')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                queryset = queryset.filter(due_date=due_date_obj)
            except ValueError:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Statistikalar
        user = request.user
        total_homeworks = self.get_queryset().count()
        active_homeworks = self.get_queryset().filter(is_active=True).count()
        today = timezone.now().date()
        upcoming_homeworks = self.get_queryset().filter(
            due_date__gte=today, is_active=True
        ).count()
        overdue_homeworks = self.get_queryset().filter(
            due_date__lt=today, is_active=True
        ).count()
        
        response.data = {
            'stats': {
                'total_homeworks': total_homeworks,
                'active_homeworks': active_homeworks,
                'upcoming_homeworks': upcoming_homeworks,
                'overdue_homeworks': overdue_homeworks,
            },
            'results': response.data
        }
        
        return response


class TeacherHomeworkDetailAPIView(RetrieveUpdateDestroyAPIView):
    """
    Teacher uchun uy vazifasi detail view
    """
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role != "teacher":
            return Homework.objects.none()
        
        return Homework.objects.filter(teacher=user)


class DashboardStatsAPIView(APIView):
    """
    Dashboard statistikasi
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        center = user.center
        
        stats = {
            'total_students': 0,
            'active_students': 0,
            'total_teachers': 0,
            'active_teachers': 0,
            'total_homeworks': 0,
            'active_homeworks': 0,
            'upcoming_homeworks': 0,
            'overdue_homeworks': 0,
            'total_payments': 0,
            'pending_payments': 0,
            'total_news': 0,
            'total_grades': 0,
            'average_grade': 0,
            'total_attendance': 0,
            'today_attendance': 0,
        }
        
        # Superadmin uchun global statistikalar
        if user.role == "superadmin":
            from account.models import User
            
            stats['total_students'] = Student.objects.count()
            stats['active_students'] = Student.objects.filter(is_active=True).count()
            stats['total_teachers'] = User.objects.filter(role="teacher").count()
            stats['active_teachers'] = User.objects.filter(role="teacher", is_active=True).count()
            stats['total_homeworks'] = Homework.objects.count()
            stats['active_homeworks'] = Homework.objects.filter(is_active=True).count()
            
            today = timezone.now().date()
            stats['upcoming_homeworks'] = Homework.objects.filter(
                due_date__gte=today,
                is_active=True
            ).count()
            stats['overdue_homeworks'] = Homework.objects.filter(
                due_date__lt=today,
                is_active=True
            ).count()
            
            stats['total_payments'] = Payment.objects.count()
            stats['pending_payments'] = Payment.objects.filter(status='pending').count()
            stats['total_news'] = News.objects.count()
            
            # Baholar statistikasi
            grade_avg = Grade.objects.aggregate(Avg('score'))['score__avg']
            stats['total_grades'] = Grade.objects.count()
            stats['average_grade'] = round(grade_avg, 2) if grade_avg else 0
            
            # Davomat statistikasi
            stats['total_attendance'] = Attendance.objects.count()
            stats['today_attendance'] = Attendance.objects.filter(
                created_at__date=today
            ).count()
        
        # Admin, admin_mini va Teacher uchun o'z markazi statistikasi
        elif user.role in ["admin", "admin_mini", "teacher"] and center:
            from account.models import User
            
            stats['total_students'] = Student.objects.filter(center=center).count()
            stats['active_students'] = Student.objects.filter(center=center, is_active=True).count()
            stats['total_teachers'] = User.objects.filter(center=center, role="teacher").count()
            stats['active_teachers'] = User.objects.filter(center=center, role="teacher", is_active=True).count()
            
            # Uy vazifalari statistikasi
            if user.role == "teacher":
                stats['total_homeworks'] = Homework.objects.filter(teacher=user).count()
                stats['active_homeworks'] = Homework.objects.filter(teacher=user, is_active=True).count()
                
                today = timezone.now().date()
                stats['upcoming_homeworks'] = Homework.objects.filter(
                    teacher=user,
                    due_date__gte=today,
                    is_active=True
                ).count()
                stats['overdue_homeworks'] = Homework.objects.filter(
                    teacher=user,
                    due_date__lt=today,
                    is_active=True
                ).count()
            else:
                stats['total_homeworks'] = Homework.objects.filter(center=center).count()
                stats['active_homeworks'] = Homework.objects.filter(center=center, is_active=True).count()
                
                today = timezone.now().date()
                stats['upcoming_homeworks'] = Homework.objects.filter(
                    center=center,
                    due_date__gte=today,
                    is_active=True
                ).count()
                stats['overdue_homeworks'] = Homework.objects.filter(
                    center=center,
                    due_date__lt=today,
                    is_active=True
                ).count()
            
            # To'lovlar statistikasi
            stats['total_payments'] = Payment.objects.filter(student__center=center).count()
            stats['pending_payments'] = Payment.objects.filter(
                student__center=center,
                status='pending'
            ).count()
            
            # Yangiliklar statistikasi
            stats['total_news'] = News.objects.filter(center=center).count()
            
            # Baholar statistikasi
            if user.role == "teacher":
                stats['total_grades'] = Grade.objects.filter(teacher=user).count()
                grade_avg = Grade.objects.filter(teacher=user).aggregate(Avg('score'))['score__avg']
            else:
                stats['total_grades'] = Grade.objects.filter(student__center=center).count()
                grade_avg = Grade.objects.filter(student__center=center).aggregate(Avg('score'))['score__avg']
            
            stats['average_grade'] = round(grade_avg, 2) if grade_avg else 0
            
            # Davomat statistikasi
            if user.role == "teacher":
                stats['total_attendance'] = Attendance.objects.filter(teacher=user).count()
                stats['today_attendance'] = Attendance.objects.filter(
                    teacher=user,
                    created_at__date=timezone.now().date()
                ).count()
            else:
                stats['total_attendance'] = Attendance.objects.filter(student__center=center).count()
                stats['today_attendance'] = Attendance.objects.filter(
                    student__center=center,
                    created_at__date=timezone.now().date()
                ).count()
        
        return Response(stats)


class StudentGradesAPIView(ListAPIView):
    """
    O'quvchining baholari
    """
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        user = self.request.user
        
        queryset = Grade.objects.filter(student_id=student_id)
        
        if user.role == "teacher":
            queryset = queryset.filter(teacher=user)
        elif user.role in ["admin", "admin_mini"]:
            queryset = queryset.filter(student__center=user.center)
        
        return queryset


class StudentAttendanceAPIView(ListAPIView):
    """
    O'quvchining davomatlari
    """
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        user = self.request.user
        
        queryset = Attendance.objects.filter(student_id=student_id)
        
        if user.role == "teacher":
            queryset = queryset.filter(teacher=user)
        elif user.role in ["admin", "admin_mini"]:
            queryset = queryset.filter(student__center=user.center)
        
        return queryset


class StudentPaymentsAPIView(ListAPIView):
    """
    O'quvchining to'lovlari
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        student_id = self.kwargs.get('student_id')
        user = self.request.user
        
        queryset = Payment.objects.filter(student_id=student_id)
        
        if user.role in ["admin", "admin_mini", "superadmin"]:
            pass  # Barcha to'lovlarni ko'rish mumkin
        else:
            queryset = queryset.none()
        
        return queryset


class TeacherStudentListAPIView(ListAPIView):
    """
    Teacher'ning o'quvchilari ro'yxati
    """
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role != "teacher":
            return Student.objects.none()
        
        return Student.objects.filter(teacher=user, is_active=True)


class TeacherAttendanceListAPIView(ListAPIView):
    """
    Teacher'ning davomatlari ro'yxati
    """
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role != "teacher":
            return Attendance.objects.none()
        
        return Attendance.objects.filter(teacher=user)


class TeacherGradeListAPIView(ListAPIView):
    """
    Teacher'ning baholari ro'yxati
    """
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role != "teacher":
            return Grade.objects.none()
        
        return Grade.objects.filter(teacher=user)