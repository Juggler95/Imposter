from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    class Roles(models.TextChoices):
        NONE = 'none'
        STANDARD = 'standard'
        IMPOSTER = 'imposter'
    role = models.CharField(choices=Roles, default=Roles.NONE, max_length=10)
    current_room = models.ForeignKey("Room", on_delete=models.CASCADE, null=True, blank=True, related_name="current_room" )

class Room(models.Model):
    code = models.TextField(max_length=10, blank=False, null=False)
    current_player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name="room_current_player")
    first_player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name="room_first_player")
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name="room_host_user")
    imposter_count = models.PositiveIntegerField(default=1)
    is_running = models.BooleanField(default=False)
    players = models.ManyToManyField(User, blank=True, null=True, related_name="room_players")
    rounds = models.PositiveIntegerField(default=3)

# class Roles(models.Model):
#     room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=False, related_name="room_roles")

