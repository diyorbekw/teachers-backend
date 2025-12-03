# core/views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import (
    LearningCenter, Parent, Student, 
    Attendance, Grade, Payment, News
)
from .serializers import (
    LearningCenterSerializer, ParentSerializer,
    StudentSerializer, AttendanceSerializer,
    GradeSerializer, PaymentSerializer, NewsSerializer
)


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