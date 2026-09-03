from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    pass

class Room(models.Model):
    code = models.TextField(max_length=10, blank=False, null=False)
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name="room_host_user")
    players = models.ManyToManyField(User, blank=True, null=True, related_name="room_players")
    rounds = models.PositiveIntegerField(default=3)
    imposter_count = models.PositiveIntegerField(default=1)
