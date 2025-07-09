from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'phone_number', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name')
