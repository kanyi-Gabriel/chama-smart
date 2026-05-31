from django.db import models
from accounts.models import User
from chamas.models import Chama


class LoanApplication(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('repaid', 'Repaid'),
        ('defaulted', 'Defaulted'),
    ]

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='loan_applications')
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ml_credit_score = models.FloatField(null=True, blank=True)
    ml_recommendation = models.CharField(max_length=20, null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_loans')
    repayment_period_months = models.PositiveIntegerField(default=3)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    def __str__(self):
        return f"{self.applicant} | KES {self.amount_requested} | {self.status}"


class LoanRepayment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='repayments')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_repayments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_reference = models.CharField(max_length=50, blank=True, null=True, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member} repaid KES {self.amount} | {self.status}"