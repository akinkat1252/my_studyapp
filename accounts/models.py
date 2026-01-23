from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class Language(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return f"{self.name}"


class CustomUser(AbstractUser):
    user_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="native_users",
        null=True,
        blank=True,
    )
    interest_category = models.ManyToManyField(
        'task_management.Category',
        through='task_management.UserInterestCategory',
        related_name='interested_users',
    )
    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
