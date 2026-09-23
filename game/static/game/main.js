document.addEventListener("DOMContentLoaded", () => {
  const leaveRoomBtn = document.getElementById("leave-room-btn");
  leaveRoomBtn?.addEventListener("click", function () {
    const container = this.parentNode;
    if(confirm('Are you sure you want to leave the room?')){
      leaveRoom(container.dataset.room_id);
    }else{
      return false;
    }
  });

  const closeRoomBtn = document.getElementById("close-room-btn");
  closeRoomBtn?.addEventListener("click", function () {
    const container = this.parentNode;
    if(confirm('Are you sure you want to close room?')){
      closeRoom(container.dataset.room_id);
    }else{
      return false;
    }
  });

  const startRoomBtn = document.getElementById('start-room-btn');
  startRoomBtn?.addEventListener("click", function() {
    const container = this.parentNode;
    const player_selector = document.getElementById('starting-player-selector');
    const players = document.getElementById('starting-player-selector').dataset.players;
    if(confirm('Are you sure you want to start the room?')){
      console.log(players);
      startRoom(container.dataset.room_id, player_selector);
    }else{
      return false;
    }
  });

  const endGameBtn = document.getElementById('end-game-btn');
  endGameBtn?.addEventListener("click", function() {
    if(confirm('Are you sure you want to end the game?')){
      endGame(this.dataset.room_id);
    }else{
      return false;
    }
  });

  document.querySelectorAll('.categories').forEach((button) => {
    button.addEventListener('click', function() {
      const container = button.parentNode
      if (button.getAttribute("id") === 'point'){
        select_category(container.dataset.room_id, 'point')
      }else if (button.getAttribute("id") === 'words'){
        select_category(container.dataset.room_id, 'words')
      }else if (button.getAttribute("id") === 'fingers'){
        select_category(container.dataset.room_id, 'fingers')
      }else if (button.getAttribute("id") === 'hands'){
        select_category(container.dataset.room_id, 'hands')
      }
    });
  });

  if(document.getElementById('redirect-to-game') !== null){
    window.location.href = `game/${document.getElementById('redirect-to-game').dataset.room_id}`
  }

  document.querySelectorAll('.vote-btn').forEach((button) => {
    button.addEventListener('click', function() {
      const container = button.parentNode
      console.log(button.dataset.vote_player);
      // console.log(container.dataset.current_user);
    });
  });
});

async function closeRoom(room_id) {
  const url = `room_control/${room_id}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        command: "close",
      }),
      headers: { "X-CSRFToken": csrftoken },
      mode: "same-origin",
    });
    if (!response.ok){
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result);
    window.location.href = "/";
  } catch (error) {
    console.error(error.message);
  }
}

async function endGame(room_id){
  const url = `/game_control/${room_id}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        command: "end_game",
      }),
      headers: { "X-CSRFToken": csrftoken },
      mode: "same-origin",
    });
    if (!response.ok){
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result);
    if (result.success === "Game ended successfully"){
      window.location.href = window.location.href;
    }
  } catch (error) {
    console.error(error);
  }
}

async function leaveRoom(room_id) {
  const url = `room_control/${room_id}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        command: "leave",
      }),
      headers: { "X-CSRFToken": csrftoken },
      mode: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result);
    if (result.success === "You left the room successfully") {
      window.location.href = "/";
    }
  } catch (error) {
    console.error(error.message);
    if (error.message === "Response status: 403") {
      // this means the user is already not in the room and should be redirect back to the index page
      window.location.href = "/";
    }
  }
}

async function startRoom(room_id, player_selector){
  const players = player_selector.dataset.players;
  const first_player = player_selector.value;

  const url = `room_control/${room_id}`;
  try{
    if(players.includes(first_player) === false){
      throw new Error(`Selected first player is not valid player`);
    }
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        command: "start",
        players: players,
        first_player: first_player
      }),
      headers: { "X-CSRFToken": csrftoken },
      mode: "same-origin",
    })

    if (!response.ok){
      output = await response.json();
      if (output.error === "Player is not in frontend players list but is in backend" || output.error === "Player is in frontend players list but not in backend"){
        alert(`${output.error}. Please try to start the game again`);
        window.location.href = window.location.href;
      }
      throw new Error(`Response status:`)
    }
    
    const result = await response.json();
    console.log(result);
    if (result.success === "You started the room successfully"){
      window.location.href = window.location.href;
    }

  }catch(error){
    console.error(error.message);
  }
}

async function select_category(room_id, category){
  const url = `game_control/${room_id}`
  try{
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        command: "select_category",
        category: category
      }),
      headers: { "X-CSRFToken": csrftoken },
      mode: "same-origin",
    })

    if (!response.ok){
      throw new Error(`Response status:`)
    }
    
    const result = await response.json();
    if (result.success){
      window.location.href = `game/${room_id}`
    }
    console.log(result);
  }catch(error){
    console.error(error);
  }
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie("csrftoken");
