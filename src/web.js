// Polyfill for requestVideoFrameCallback in case the browser doesnt support it
import '../node_modules/rvfc-polyfill/index.js';

/**
 * Stream the user's webcam to the given
 * video element.
 * 
 * @param {HTMLVideoElement} video video element to show user's webcam
 */
function getVideoFromWebcam(video) {
  // Access the user's webcam
  navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      facingMode: "user"
    }
  }).then((stream) => {
    video.src = null;
    video.srcObject = stream;
  }).catch((error) => {
    console.log("Rejected!", error);
  });
}

/**
 * Stream the the given video file from user input
 * to the given video element.
 * 
 * @param {HTMLVideoElement} video video element to show the given video file
 */
function getVideoFromFile(video) {
  const input = document.createElement('input');
  input.type = 'file';

  input.onchange = (e) => {
    const file = e.target.files[0];

    if (file) {
      const url = URL.createObjectURL(file);
      const reader = new FileReader();

      reader.onload = function () {
        video.src = url;
        video.srcObject = null;
        video.play();
      }

      reader.readAsDataURL(file);
    }
  }

  input.click();
}

/**
 * Track every keypress and check if it matches
 * certain key with these conditions:
 * 
 * if its "p" key then play/pause the video
 * if its "q" key then get video from webcam
 * if its " " key then get video from file
 */
window.addEventListener("keydown", (event) => {
  // Get the video html tag element
  const video = document.querySelector("video");

  switch (event.key.toLowerCase()) {
    case "p":
      if (video.paused) {
        video.play();
      } else {
        video.pause();
      }
      break;

    case " ": // space
      getVideoFromFile(video);
      break;

    case "q":
      getVideoFromWebcam(video);
      break;
  }
})

// Run everything once the webpage loaded
window.onload = () => {
  // Get the video html tag element
  const video = document.querySelector("video");

  getVideoFromWebcam(video);

  // Create a canvas element and get the context
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  // Open websocket connection on the specified URL
  const socket = new WebSocket("ws://localhost:1337");
  let isSocketOpened = false;

  // Set video size to match the screen size
  Object.assign(video.style, {
    width: `${screen.width}px`,
    height: `${screen.height}px`,
    "object-fit": "cover"
  });

  // Fix canvas resolution
  // Ref: https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio#correcting_resolution_in_a_canvas
  const scale = window.devicePixelRatio;
  const fixedScreenWidth = (screen.width * scale)
  const fixedScreenHeight = (screen.height * scale)

  // Set canvas size to 10x smaller than screen for faster websocket message sending
  canvas.width = Math.floor(fixedScreenWidth / 10);
  canvas.height = Math.floor(fixedScreenHeight / 10);

  // Get current window's position
  let curScreenLeft = window.screenLeft,
    curScreenTop = window.screenTop;

  // Set initial transformation
  video.style.transform = `translate(-${curScreenLeft}px, -${curScreenTop}px)`;

  // Main loop to move the video according to the browser window's position
  (function dynamicallyMoveVideo() {
    let newScreenLeft = window.screenLeft;
    let newScreenTop = window.screenTop;

    if (newScreenLeft !== curScreenLeft || newScreenTop !== curScreenTop) {
      // Translate/Move the video to certain position using css transform style
      video.style.transform = `translate(-${newScreenLeft}px, -${newScreenTop}px)`;

      curScreenLeft = newScreenLeft;
      curScreenTop = newScreenTop;
    }

    window.requestAnimationFrame(dynamicallyMoveVideo);
  })();

  socket.addEventListener("open", () => {
    isSocketOpened = true;
  });

  // Main loop to get the current frame from the video and put it in the canvas
  // that will later sent through the websocket to the cli application
  (function sendFrame() {
    // Grab the whole frame from the video and paint it on the canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    if (isSocketOpened && socket.readyState == socket.OPEN) {
      // Grab the base64 encoded frame from the canvas and send it 
      // through websocket if the websocket connection has been opened
      const base64EncodedFrame = canvas.toDataURL().split(';base64,')[1];
      socket.send(base64EncodedFrame)
    }

    video.requestVideoFrameCallback(sendFrame);
  })();
}