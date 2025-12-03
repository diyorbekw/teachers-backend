# project_name/swagger_config.py
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg import openapi


class CustomAutoSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        """API endpoint'larini guruhlash uchun tag'lar"""
        tags = super().get_tags(operation_keys)
        
        if 'users' in operation_keys:
            return ['Users']
        elif 'learning-centers' in operation_keys:
            return ['Learning Centers']
        elif 'parents' in operation_keys:
            return ['Parents']
        elif 'students' in operation_keys:
            return ['Students']
        elif 'attendances' in operation_keys:
            return ['Attendances']
        elif 'grades' in operation_keys:
            return ['Grades']
        elif 'payments' in operation_keys:
            return ['Payments']
        elif 'news' in operation_keys:
            return ['News']
        elif 'token' in operation_keys:
            return ['Authentication']
        
        return tags
    
    def get_operation(self, operation_keys):
        """Operation ma'lumotlarini o'zgartirish"""
        operation = super().get_operation(operation_keys)
        
        # CRUD amallari uchun description qo'shish
        if operation_keys[-1] == 'list':
            operation.summary = f"Get list of {operation_keys[-2]}"
        elif operation_keys[-1] == 'create':
            operation.summary = f"Create new {operation_keys[-2].rstrip('s')}"
        elif operation_keys[-1] == 'retrieve':
            operation.summary = f"Get {operation_keys[-2].rstrip('s')} details"
        elif operation_keys[-1] == 'update':
            operation.summary = f"Update {operation_keys[-2].rstrip('s')}"
        elif operation_keys[-1] == 'partial_update':
            operation.summary = f"Partial update of {operation_keys[-2].rstrip('s')}"
        elif operation_keys[-1] == 'destroy':
            operation.summary = f"Delete {operation_keys[-2].rstrip('s')}"
        
        return operation


# Token obtain uchun schema
token_obtain_schema = {
    "phone_number": openapi.Schema(
        title="Phone number",
        type=openapi.TYPE_STRING,
        description="Foydalanuvchi telefon raqami",
        example="+998901234567"
    ),
    "password": openapi.Schema(
        title="Password",
        type=openapi.TYPE_STRING,
        format=openapi.FORMAT_PASSWORD,
        description="Foydalanuvchi paroli"
    ),
}