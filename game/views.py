import json
import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt


from .models import User, Room

POINT = ['Point a the the person to your left', 'Point at the person you think knows the most digits of pi']
HANDS = ['Raise your hand if your name starts with a letter between "A-M" in the alphabet', 'Raise your hand if your name starts with a letter between "N-A" in the alphabet']
FINGERS = ["Raise 0 fingers", "Raise the amount of fingers as reality shows you are currently invested into"]
WORDS = ["Name your favorite Super Hero", "Say something you enjoy doing"]
IMPOSTER_WORDS = ["Name a character that has Super Powers", "Say something you don't enjoy doing"]

# Create your views here.
@login_required(login_url='login')
def index(request):
    message = ''
    if 'redirect-message' in request.session:
        message = request.session['redirect-message']
        del request.session['redirect-message']


    user = User.objects.get(pk=request.user.id)

    if not user.current_room == None:
        return redirect('room', room_id=user.current_room.id)
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
        if not request.user.current_room == None:
            return redirect('room', room_id=request.user.current_room.id)
        return render(request, 'game/create_room.html')

@login_required(login_url='login')
def game_view(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
        user = User.objects.get(pk=request.user.id)
        players = list(room.players.values_list('username', flat=True))
        is_host = False
        if user == room.host:
            is_host = True

        if room.voting:
            return redirect('vote', room_id=room_id)

        if user.username not in players and not user == room.host:
            request.session['redirect-message'] = 'You are not a player in this room'
            return redirect('index')

        if room.selected_category == 'none':
            room.card_index = None
            room.selected_category = None
            room.save()
            # return redirect(f'{request.META.get('HTTP_REFERER')}')
            return redirect(f'/room:{room_id}')

        if room.is_running == False:
            room.card_index = None
            room.selected_category = None
            room.save()
            return redirect(f'/room:{room_id}')

        card = ''
        imposter_card = 'Your the imposter. Try to blend in'
        # save card index to DB so it is synced to all players
        if room.selected_category == 'point':
            index = None
            if room.card_index != None:
                index = room.card_index
            else:
                index = random.randrange(len(POINT))
                room.card_index = index
                room.save()
            card = POINT[index]

        elif room.selected_category == 'hands':
            index = None
            if room.card_index != None:
                index = room.card_index
            else:
                index = random.randrange(len(HANDS))
                room.card_index = index
                room.save()
            card = HANDS[index]
        elif room.selected_category == 'fingers':
            index = None
            if room.card_index != None:
                index = room.card_index
            else:
                index = random.randrange(len(FINGERS))
                room.card_index = index
                room.save()
            card = FINGERS[index]
        elif room.selected_category == 'words':
            index = None
            if room.card_index != None:
                index = room.card_index
            else:
                index = random.randrange(len(WORDS))
                room.card_index = index
                room.save()
            card = WORDS[index]
            imposter_card = IMPOSTER_WORDS[index]

        return render(request, 'game/game.html', {
            'is_host': is_host,
            'host': room.host,
            'players': players,
            'room': room,
            'card': card,
            'imposter_card': imposter_card
        })
    except Room.DoesNotExist:
        print('Room not found')
        request.session['redirect-message'] = 'Room not found'
        return redirect('index')

@login_required(login_url='login')
def game_control(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room with provided id does not exist'}, status=404)
    body = json.loads(request.body)
    command = body.get('command')

    def set_room_roles():
        players = list(room.players.all())
        def set_roles(player, role):
            player.role = User.Roles.NONE
            player.save()

            player.role = role
            player.current_room = room
            player.save()

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
                set_roles(player, User.Roles.IMPOSTER)

            else:
                player = User.objects.get(username=players[i])
                # reset old roles before giving new one.
                set_roles(player, User.Roles.STANDARD)

    def select_category():
        category = body.get('category')
        if request.user == room.current_player:
            if category == 'point':
                room.selected_category = room.Categories.POINT
                room.save()
                return {"success": "Set category to point successfully"}
            elif category == 'words':
                room.selected_category = room.Categories.WORDS
                room.save()
                return {"success": "Set category to words successfully"}
            elif category == 'fingers':
                room.selected_category = room.Categories.FINGERS
                room.save()
                return {"success": "Set category to fingers successfully"}
            elif category == 'hands':
                room.selected_category = room.Categories.HANDS
                room.save()
                return {"success": "Set category to hands successfully"}
            else:
                room.selected_category = room.Categories.NONE
                room.save()
                return {"error": "Unknown category"}
        else:
            return {"error": "User request was not from current player"}

    def end_game():
        players = list(room.players.values_list('username', flat=True))
        for p in players:
            player = User.objects.get(username=p)
            player.role = User.Roles.NONE
            player.current_room = None
            player.votes = 0
            player.voted = None
            player.save()
        room.first_player = None
        room.is_running = False
        room.selected_category = room.Categories.NONE
        room.card_index = None
        room.voting = False
        room.save()

    if room.is_running:
        if command == 'start':
            set_room_roles()
            return JsonResponse({"success": "Roles have been set successfully"}, status=201)
        elif command == 'select_category':
            output = select_category()
            if output == None:
                return JsonResponse({"error": "Select category returned output of None"}, status=400)
            elif 'success' in output.keys():
                return JsonResponse({"success": f"{output['success']}"}, status=201)
            elif 'error' in output.keys():
                return JsonResponse({"error": f"{output['error']}"}, status=403)
            else:
                return JsonResponse({"error": "output returned unknown key"}, status=400)
        elif command == 'vote':
            if request.user.voted == None:
                try:
                    # print(f'voted for player {body.get('voted_player')}')
                    vp = body.get('voted_player')
                    print(f'VP {vp}')
                    voted_player = User.objects.get(username=vp)
                except User.DoesNotExist:
                    print(User.objects.get(username=body.get('voted_player')))
                    return JsonResponse({"error": "voted player does not exist"}, status=400)
                if voted_player == request.user:
                    return JsonResponse({'error': f"You cannot vote for yourself"}, status=400)
                voted_player.votes += 1
                request.user.voted = voted_player
                voted_player.save()
                request.user.save()
                print(voted_player.votes)
                print(request.user.voted)
                return JsonResponse({'success': f"successfully voted for {voted_player.username}"}, status=201)
            else:
                return JsonResponse({'error': f"You already have voted. You cannot vote twice"}, status=400)
        elif command == 'end_game':
            end_game()
            return JsonResponse({"success": "Game ended successfully"}, status=201)

@login_required(login_url='login')
def join_room(request):
    if request.method == 'GET':
        try:
            user = User.objects.get(pk=request.user.id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User does not exist"})
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

@login_required(login_url='login')
def room_control(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room does not exist'}, status=404)

    if request.method == "POST":
        try:
            user = User.objects.get(pk=request.user.id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=400)

        body = json.loads(request.body)
        command = body.get('command')
        players = body.get('players') if body.get('players') else None
        if command == 'leave':
            if user == room.host:
                return JsonResponse({"error": "You are host, can't leave room"}, status=400)
            for player in room.players.all():
                if user == player:
                    room.players.remove(user)
                    room.save()
                    players = list(room.players.values_list('username', flat=True))
                    for p in players:
                        player = User.objects.get(username=p)
                        player.role = User.Roles.NONE
                        player.save()
                        # player.current_room = None
                    return JsonResponse({"success": "You left the room successfully"}, status=201)

            return JsonResponse({"error": "You are not in this room"}, status=403)
        elif command == 'close':
            if user == room.host:
                room.delete()
                return JsonResponse({"success": "You closed the room successfully"}, status=201)
        elif command == 'start':
            if user == room.host and room.is_running == False:
                players_list = list()
                # list taken from javascript body is seperated by each character
                # this part of the code converts that broken list into a python list containing each player name
                if players != None:
                    player_str = ""
                    in_word = False
                    for c in players:
                        if not in_word:
                            if c == '\'':
                                in_word = True
                        else:
                            if c == '\'':
                                players_list.append(player_str)
                                player_str = ""
                                in_word = False
                            else:
                                player_str += c


                # Player de-sync checks
                backend_players = list(room.players.all())
                backend_players_usernames = list()

                # check frontned for desync with users in the backend
                for p in backend_players:
                    backend_players_usernames.append(p.username)

                if len(backend_players_usernames) != len(players_list):
                    return JsonResponse({"error": f"Player is not in frontend players list but is in backend"}, status=400)

                # check if backend has anying players not in the frontend
                # this is for if a player leaves and the frontend hasn't updated yet but that backend has
                for name in players_list:
                    if name not in backend_players_usernames:
                        return JsonResponse({"error": f"Player is in frontend players list but not in backend"}, status=400)

                # set and valididate first player
                first_player = body.get('first_player')
                if first_player != None:
                    # validiate first player is a valid player
                    if first_player in players_list:
                        # set first player
                        room.first_player = User.objects.get(username=first_player)
                    else:
                        return JsonResponse({"error": f"The given first player was not in the players_list"}, status=400)
                else:
                    return JsonResponse({"error": f"first player gave returned None"}, status=400)


                room.current_player = User.objects.get(username=first_player)
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

        if room.voting:
            return redirect('vote', room_id=room_id)

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

@login_required(login_url='login')
def vote_view(request, room_id):
    if request.method == 'GET':
        try:
            room = Room.objects.get(pk=room_id)
            players = list(room.players.values_list('username', flat=True))
            user = User.objects.get(pk=request.user.id)
            is_host = False
            if user == room.host:
                is_host = True

            if room.is_running:
                room.voting = True
                room.save()
        except Room.DoesNotExist:
            request.session['redirect-message'] = 'Room not found'
            return redirect('index')
        if request.user.username not in players and not request.user == room.host:
            request.session['redirect-message'] = 'You are not a player in this room'
            return redirect('index')
        if not room.is_running:
            return redirect('room', room_id=room.id)
        return render(request, 'game/vote.html', {
            'room': room,
            'players': players,
            'is_host': is_host,
            'user': user
        })
    else:
        return redirect('index')
