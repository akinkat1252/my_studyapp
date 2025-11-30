from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class CustomUser(AbstractUser):
    interest_category = models.ManyToManyField(
        'task_management.Category',
        through='task_management.UserInterestCategory',
        related_name='interested_users',
    )
    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
