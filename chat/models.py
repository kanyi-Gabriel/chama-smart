from django.db import models
from accounts.models import User
from chamas.models import Chama


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('announcement', 'Announcement'),
        ('system', 'System'),
    ]

    chama = models.ForeignKey(
        Chama, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='messages'
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MESSAGE_TYPES, default='text'
    )
    is_pinned = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} → {self.chama}: {self.content[:50]}"