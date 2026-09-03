from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render


from .models import User, Room

# Create your views here.
@login_required(login_url='login')
def index(request):
    user = User.objects.get(pk=request.user.id)
    rooms = Room.objects.all()
    for room in rooms:
        players = room.players.values_list('username', flat=True)
        if user.username in players:
            return render(request, 'game/index.html', {
                'room': room
            })

    return render(request, 'game/index.html')

@login_required(login_url='login')
def create_room(request):
    if request.method == 'POST':
        host = User.objects.get(pk=request.user.id) 
        code = request.POST['create_code']
        try:
            rounds = int(request.POST['rounds'])
            imposter_count = int(request.POST['imposter_count'])
        except:
            return render(request, 'game/create_room.html', {
                "message": 'Could not cast rounds/imposter_count to int'
            })
        if imposter_count < 1:
            return render(request, 'game/create_room.html', {
                "message": 'Imposter count can not be less than 1'
            })
        elif rounds < 1:
            return render(request, 'game/create_room.html', {
                "message": 'Rounds can not be less than 1'
            })
        elif len(code) < 4 or len(code) > 10:
            return render(request, 'game/create_room.html', {
                "message": 'Invalid code length.'
            })

        room = Room.objects.create(host=host, code=code, imposter_count=imposter_count, rounds=rounds)
        room.save()
        room.players.add(host)
        return HttpResponse(f'host: {host}, code: {code}, imposter count: {imposter_count}, rounds: {rounds}, players: {room.players.all()}')
    else:
        return render(request, 'game/create_room.html')

def join_room(request):
    if request.method == 'GET':
        user = User.objects.get(pk=request.user.id)
        code = request.GET.get('join_code')
        try:
            room = Room.objects.get(code=code)
            players = room.players.all()
            if user in players:
                # probably should redirect the user back to the room if they are already in it
                return redirect('room', room_id=room.id)
            room.players.add(user)
            return redirect('room', room_id=room.id)
        except Room.DoesNotExist:
            return render(request, 'game/index.html', {
                'message': "No room with given code"
            })

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'game/login.html', {
                'message': 'Invalid username and/or password.'
            })
    else:
        return render(request, 'game/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirmation = request.POST['confirmation']

        if password != confirmation:
            return render(request, 'game/register.html', {
                'message': 'Password does not match confirmation.'
            })
        
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, 'game/register.html', {
                'message': 'Username already taken.'
            })
        login(request, user)
        return redirect('index')
    else:
        return render(request, 'game/register.html')

def room_view(request, room_id):
    room = Room.objects.get(pk=room_id)
    user = User.objects.get(pk=request.user.id)
    players = list(room.players.values_list('username', flat=True))
    is_host = False
    if user == room.host:
        is_host = True

    return render(request, 'game/room.html', {
        'is_host': is_host,
        'host': room.host,
        'players': players,
        'room': room
    })
    # return HttpResponse(f'Host: {room.host}, Code: {room.code}, Players: {players}, Imposter count: {room.imposter_count}, Rounds: {room.rounds}')
