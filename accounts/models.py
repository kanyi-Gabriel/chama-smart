from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_set',
        blank=True
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"