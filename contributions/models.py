from django.db import models
from accounts.models import User
from chamas.models import Chama


class Contribution(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mpesa_reference = models.CharField(max_length=50, blank=True, null=True, unique=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    penalty_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} → {self.chama} | KES {self.amount} | {self.status}"


class Penalty(models.Model):

    contribution = models.OneToOneField(Contribution, on_delete=models.CASCADE, related_name='penalty')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='penalties')
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='penalties')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    reason = models.TextField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Penalty: {self.member} | KES {self.amount} | Paid: {self.is_paid}"