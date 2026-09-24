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
    votes = models.PositiveIntegerField(default=0)
    voted = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True, related_name="voted_player")


class Room(models.Model):
    class Categories(models.TextChoices):
        NONE = 'none'
        POINT = 'point'
        HANDS = 'hands'
        FINGERS = 'fingers'
        WORDS = 'words'
    code = models.TextField(max_length=10, blank=False, null=False)
    current_player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name="room_current_player")
    card_index = models.PositiveIntegerField(null=True, blank=True)
    first_player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="room_first_player")
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False, related_name="room_host_user")
    imposter_count = models.PositiveIntegerField(default=1)
    is_running = models.BooleanField(default=False)
    players = models.ManyToManyField(User, blank=True, null=True, related_name="room_players")
    rounds = models.PositiveIntegerField(default=3)
    voting = models.BooleanField(default=False)
    selected_category = models.CharField(choices=Categories, default=Categories.NONE, max_length=10, null=True, blank=True)
