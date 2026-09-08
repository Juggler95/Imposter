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
    if(confirm('Are you sure you want to start the room?')){
      startRoom(container.dataset.room_id);
    }else{
      return false;
    }
  })
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

async function startRoom(room_id){
  const url = `room_control/${room_id}`;
  try{
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        command: "start"
      }),
      headers: { "X-CSRFToken": csrftoken },
      mode: "same-origin",
    })

    if (!response.ok){
      throw new Error(`Response status:`)
    }
    
    const result = await response.json();
    console.log(result);
  }catch(error){
    console.error(error.message);
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
