from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class CustomUser(AbstractUser):

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
