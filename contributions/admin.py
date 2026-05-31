from django.contrib import admin
from .models import Contribution, Penalty

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['member', 'chama', 'amount', 'status', 'is_late', 'transaction_date']
    list_filter = ['status', 'is_late']
    search_fields = ['member__phone_number', 'mpesa_reference']

@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ['member', 'chama', 'amount', 'is_paid', 'created_at']
    list_filter = ['is_paid']