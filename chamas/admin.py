from django.contrib import admin
from .models import Chama, Membership

@admin.register(Chama)
class ChamaAdmin(admin.ModelAdmin):
    list_display = ['name', 'contribution_amount', 'frequency', 'max_members', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter = ['frequency', 'is_active']

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'chama', 'role', 'credit_score', 'date_joined', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__phone_number', 'chama__name']