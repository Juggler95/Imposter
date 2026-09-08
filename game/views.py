import json
import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt


from .models import User, Room

# Create your views here.
@login_required(login_url='login')
def index(request):
    message = ''
    if 'redirect-message' in request.session:
        message = request.session['redirect-message']
        del request.session['redirect-message']

    user = User.objects.get(pk=request.user.id)
    rooms = Room.objects.all()
    for room in rooms:
        players = room.players.values_list('username', flat=True)
        if user.username in players:
            return render(request, 'game/index.html', {
                'room': room,
                'message': message
            })


    return render(request, 'game/index.html', {
        'message': message
    })

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

        for room in Room.objects.all():
            if host == room.host:
                request.session['redirect-message'] = f'You are already the host of another room with code: {room.code}'
                return redirect('index')
            elif host in room.players.all():
                request.session['redirect-message'] = f'You are already a player in another room with host: {room.host} and code: {room.code}'
                return redirect('index')
        room = Room.objects.create(host=host, code=code, imposter_count=imposter_count, rounds=rounds)
        room.save()
        room.players.add(host)
        # return HttpResponse(f'host: {host}, code: {code}, imposter count: {imposter_count}, rounds: {rounds}, players: {room.players.all()}')
        return redirect('room', room_id=room.id)
    else:
        return render(request, 'game/create_room.html')

@login_required(login_url='login')
def game_control(request, room_id):
    room = Room.objects.get(pk=room_id)
    if room.is_running:
        players = list(room.players.all())
        imposters_indices = list()
        for _ in range(room.imposter_count):
            loop = True
            while loop:
                loop = False
                index = random.randrange(len(players))
                if index in imposters_indices:
                    loop = True
                else:
                    imposters_indices.append(index)
        for i in range(len(players)):
            if i in imposters_indices:
                player = User.objects.get(username=players[i])
                player.role = User.Roles.IMPOSTER
                player.current_room = room
                player.save()
            else:
                player = User.objects.get(username=players[i])
                player.role = User.Roles.STANDARD
                player.current_room = room
                player.save()

        

@login_required(login_url='login')
def join_room(request):
    if request.method == 'GET':
        user = User.objects.get(pk=request.user.id)
        code = request.GET.get('join_code')
        try:
            room = Room.objects.get(code=code)
            if not room.is_running:
                players = room.players.all()
                if user in players:
                    # probably should redirect the user back to the room if they are already in it
                    return redirect('room', room_id=room.id)
                room.players.add(user)
                return redirect('room', room_id=room.id)
            else:
                request.session['redirect-message'] = 'Cannot join room, Room is already in progress'
                return redirect('index')
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


@login_required(login_url='login')
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

# @csrf_exempt
@login_required(login_url='login')
def room_control(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room does not exist'}, status=404)

    if request.method == "POST":
        user = User.objects.get(pk=request.user.id)
        body = json.loads(request.body)
        command = body.get('command')
        if command == 'leave':
            if user == room.host:
                return JsonResponse({"error": "You are host, can't leave room"}, status=400)
            for player in room.players.all():
                if user == player:
                    room.players.remove(user)
                    room.save()
                    return JsonResponse({"success": "You left the room successfully"}, status=201)

            return JsonResponse({"error": "You are not in this room"}, status=403)
        elif command == 'close':
            if user == room.host:
                room.delete()
                return JsonResponse({"success": "You closed the room successfully"}, status=201)
        elif command == 'start':
            if user == room.host and room.is_running == False:
                room.is_running = True
                room.save()
                game_control(request, room_id)
                return JsonResponse({"success": "You started the room successfully"}, status=201)
        else:
            return JsonResponse({'error': 'Not known command argument'}, status=400)
    else:
        return redirect('index')

@login_required(login_url='login')
def room_view(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
        user = User.objects.get(pk=request.user.id)
        players = list(room.players.values_list('username', flat=True))
        is_host = False
        if user == room.host:
            is_host = True

        if user.username not in players and not user == room.host:
            request.session['redirect-message'] = 'You are not a player in this room'
            return redirect('index')

        return render(request, 'game/room.html', {
            'is_host': is_host,
            'host': room.host,
            'players': players,
            'room': room
        })
    except Room.DoesNotExist:
        print('Room not found')
        request.session['redirect-message'] = 'Room not found'
        return redirect('index')
