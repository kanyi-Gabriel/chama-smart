from django.db import models
from accounts.models import User


class Chama(models.Model):

    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chamas')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_members = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.name


class Membership(models.Model):

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('treasurer', 'Treasurer'),
        ('secretary', 'Secretary'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    credit_score = models.FloatField(default=50.0)

    class Meta:
        unique_together = ('user', 'chama')

    def __str__(self):
        return f"{self.user} - {self.chama} ({self.role})"
    

class DrawSession(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='draw_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='started_draws')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_draws')
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    payout_reference = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.chama.name} Draw - {self.status}"


class DrawParticipant(models.Model):
    session = models.ForeignKey(DrawSession, on_delete=models.CASCADE, related_name='participants')
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    has_won_before = models.BooleanField(default=False)
    position = models.PositiveIntegerField()

    class Meta:
        unique_together = ('session', 'member')

    def __str__(self):
        return f"{self.member} in {self.session}"