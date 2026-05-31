from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone_number', 'get_full_name', 'email', 'is_phone_verified', 'is_staff']
    search_fields = ['phone_number', 'first_name', 'last_name', 'email']
    ordering = ['phone_number']

    fieldsets = UserAdmin.fieldsets + (
        ('Chama Smart Fields', {
            'fields': ('phone_number', 'id_number', 'profile_photo', 'is_phone_verified', 'date_of_birth')
        }),
    )