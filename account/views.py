# account/views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash

from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, 
    UserUpdateSerializer, ChangePasswordSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'center', 'is_active']
    search_fields = ['phone_number', 'first_name', 'last_name', 'subject']
    ordering_fields = ['id', 'phone_number', 'date_joined']
    ordering = ['-id']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if request.user.role not in ["superadmin", "admin"]:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.role == "admin":
            request.data['role'] = 'teacher'
            if not request.data.get('center') and request.user.center:
                request.data['center'] = request.user.center.id
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserSerializer(serializer.instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin":
            if instance.role != "teacher" or instance.created_by != user:
                return Response(
                    {"detail": "You can only update teachers created by you."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        if user.role == "admin":
            if instance.role != "teacher" or instance.created_by != user:
                return Response(
                    {"detail": "You can only update teachers created by you."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if request.user.role != "superadmin":
            return Response(
                {"detail": "Only superadmin can delete users."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role == "superadmin":
            return User.objects.all()
        
        elif user.role == "admin":
            return User.objects.filter(
                Q(role="teacher") & 
                (Q(created_by=user) | Q(created_by__role="superadmin"))
            )
        
        elif user.role in ["admin_mini", "teacher"]:
            return User.objects.filter(id=user.id)
        
        return User.objects.none()
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        
        if not (request.user.role == "superadmin" or request.user.id == user.id):
            return Response(
                {"detail": "You do not have permission to change this password."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Old password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            if request.user.id == user.id:
                update_session_auth_hash(request, user)
            
            return Response({"detail": "Password updated successfully."})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def teachers(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = self.filter_queryset(
            User.objects.filter(role='teacher', is_active=True)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        is_active = request.data.get('is_active')
        
        if is_active is None:
            return Response(
                {"detail": "is_active field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_user = request.user
        if current_user.role == "admin" and user.created_by != current_user:
            return Response(
                {"detail": "You can only toggle active status of users created by you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = is_active
        user.save()
        
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)