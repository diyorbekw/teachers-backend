# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Learning Center Management API",
        default_version='v1',
        description="""
        Learning Center Management System API Documentation
        
        Bu API o'quv markazlari boshqaruvi uchun ishlab chiqilgan tizimning REST API'si.
        
        ### Authentication
        Tizim JWT (JSON Web Token) orqali autentifikatsiya qilinadi.
        
        **Token olish:**
        1. `/api/token/` endpoint'ga `phone_number` va `password` yuboring
        2. Qaytgan `access` token'ni olib, boshqa so'rovlarda `Authorization` header'ida quyidagi formatda yuboring:
           ```
           Authorization: Bearer <your_access_token>
           ```
        3. Token muddati o'tganda, `/api/token/refresh/` endpoint'ga `refresh` token yuborib yangi `access` token olishingiz mumkin
        """,
        terms_of_service="https://www.learningcenter.com/terms/",
        contact=openapi.Contact(email="support@learningcenter.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('account.urls')),
    path('api/', include('core.urls')),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Swagger/OpenAPI documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml/', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
]

# Debug mode'da static va media fayllarini xizmat qilish
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)