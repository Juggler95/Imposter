from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    pass

class Room(models.Model):
    code = models.TextField(max_length=10, blank=False, null=False)
