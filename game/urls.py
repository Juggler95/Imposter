from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_room', views.create_room, name='create_room'),
    path('join_room', views.join_room, name='join'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register_view, name='register'),
    path('room:<int:room_id>', views.room_view, name='room'),
    path('room_control/<int:room_id>', views.room_control, name="room_control"),
]
