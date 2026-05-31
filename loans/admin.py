from django.contrib import admin
from .models import LoanApplication, LoanRepayment

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'chama', 'amount_requested', 'status', 'ml_credit_score', 'applied_at']
    list_filter = ['status']
    search_fields = ['applicant__phone_number']

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'loan', 'amount', 'status', 'paid_at']
    list_filter = ['status']