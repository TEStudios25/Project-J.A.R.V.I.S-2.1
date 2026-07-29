let handsInstance = null;
let gesturesActive = false;
let animFrameId = null;

let lastHandPos = null;
let lastTwoHandDist = null;

let videoDevicesList = [];
let currentDeviceIndex = 0;

function dist(p1, p2) {
  return Math.hypot(p1.x - p2.x, p1.y - p2.y);
}

function onHandResults(results) {
  const canvas = document.getElementById("gesture-canvas");
  const video = document.getElementById("webcam");
  const ctx = canvas.getContext("2d");
  const statusText = document.getElementById("gesture-status-text");

  canvas.width = canvas.clientWidth || 130;
  canvas.height = canvas.clientHeight || 88;

  // Render video frame directly to 2D Canvas to bypass DirectX hardware video overlay green box
  if (video && video.readyState >= 2) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  } else {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
    statusText.textContent = "SHOW HANDS";
    lastHandPos = null;
    lastTwoHandDist = null;
    return;
  }

  const hands = results.multiHandLandmarks;

  // Draw hand skeleton on canvas
  ctx.fillStyle = "#00f0ff";
  ctx.strokeStyle = "rgba(0, 240, 255, 0.85)";
  ctx.lineWidth = 1.5;

  hands.forEach(landmarks => {
    landmarks.forEach(lm => {
      const x = lm.x * canvas.width;
      const y = lm.y * canvas.height;
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  });

  // 1 HAND: ROTATION + ONE-HAND ZOOM (BLOOM / CONTRACT)
  if (hands.length === 1) {
    const lm = hands[0];
    const wrist = lm[0];
    const thumbTip = lm[4];
    const indexTip = lm[8];
    const middleTip = lm[12];
    const ringTip = lm[16];
    const pinkyTip = lm[20];
    
    // Normalized Hand Spread (Fingertips to Wrist, normalized by palm size)
    const palmSize = dist(wrist, lm[9]);
    const spreadSum = dist(wrist, thumbTip) + dist(wrist, indexTip) + dist(wrist, middleTip) + dist(wrist, ringTip) + dist(wrist, pinkyTip);
    const currSpread = spreadSum / (5 * Math.max(0.01, palmSize));

    // A. Detect Zoom Gestures (Bloom vs Contract)
    const isClosedFist = currSpread < 0.95;
    const isOpenPalm = currSpread > 1.38;
    
    let isZooming = false;

    if (isClosedFist) {
      statusText.textContent = "1 HAND · CONTRACT (ZOOM OUT)";
      if (window.orbApi) {
        window.orbApi.zoomBy(1.025); // Smooth continuous zoom out
      }
      isZooming = true;
    } else if (isOpenPalm) {
      statusText.textContent = "1 HAND · BLOOM (ZOOM IN)";
      if (window.orbApi) {
        window.orbApi.zoomBy(0.975); // Smooth continuous zoom in
      }
      isZooming = true;
    }

    // B. ROTATION / DRAG (Works with all poses: palm, fist, 1-2 fingers, pinch)
    // Uses Velocity-Filtering to act as a clutch during fast retreats/resets
    const currPos = { x: indexTip.x, y: indexTip.y };
    
    if (lastHandPos && window.orbApi && !isZooming) {
      const dx = currPos.x - lastHandPos.x;
      const dy = currPos.y - lastHandPos.y;
      const moveDistance = Math.hypot(dx, dy);

      // Velocity Threshold: if move is fast (reset/retreat), disengage rotation
      if (moveDistance < 0.07) {
        statusText.textContent = "DRAGGING ORB";
        window.orbApi.rotateBy(dx * 7.0, dy * 7.0);
      } else {
        statusText.textContent = "1 HAND · CLUTCH RESET";
      }
    } else if (!isZooming) {
      statusText.textContent = "1 HAND · HOVER";
    }

    lastHandPos = currPos;
    lastTwoHandDist = null;
  }
  // 2 HANDS: SPREAD / CLOSE TO ZOOM (Flawless zoom mode)
  else if (hands.length >= 2) {
    statusText.textContent = "2 HANDS · ZOOM";
    const h1 = hands[0][9];
    const h2 = hands[1][9];
    const currDist = dist(h1, h2);

    if (lastTwoHandDist && window.orbApi) {
      const factor = lastTwoHandDist / currDist;
      if (Math.abs(factor - 1.0) > 0.012) {
        window.orbApi.zoomBy(Math.max(0.88, Math.min(1.12, factor)));
      }
    }
    lastTwoHandDist = currDist;
    lastHandPos = null;
  }
}

async function refreshVideoDevicesList() {
  try {
    const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
    tempStream.getTracks().forEach(t => t.stop());

    const devices = await navigator.mediaDevices.enumerateDevices();
    videoDevicesList = devices.filter(d => d.kind === 'videoinput');
    console.log("[🎥 Cameras Found]:", videoDevicesList.map(d => d.label || d.deviceId));
  } catch (e) {
    console.warn("[Camera Refresh Warning]:", e);
  }
}

async function processVideoFrameLoop() {
  const video = document.getElementById("webcam");
  const canvas = document.getElementById("gesture-canvas");
  if (gesturesActive && video && video.readyState >= 2) {
    if (canvas) {
      const ctx = canvas.getContext("2d");
      canvas.width = canvas.clientWidth || 130;
      canvas.height = canvas.clientHeight || 88;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    }
    if (handsInstance) {
      try {
        await handsInstance.send({ image: video });
      } catch (err) {
        console.warn("Hand processing frame error:", err);
      }
    }
  }
  if (gesturesActive) {
    animFrameId = requestAnimationFrame(processVideoFrameLoop);
  }
}

async function startGestures() {
  const cameraBox = document.getElementById("camera-box");
  const video = document.getElementById("webcam");
  const btn = document.getElementById("btn-gesture");

  cameraBox.classList.add("active");
  btn.textContent = "INIT...";

  try {
    if (!videoDevicesList.length) {
      await refreshVideoDevicesList();
    }

    handsInstance = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });
    handsInstance.setOptions({
      maxNumHands: 2,
      modelComplexity: 1,
      minDetectionConfidence: 0.45,
      minTrackingConfidence: 0.45
    });
    handsInstance.onResults(onHandResults);

    // Pick camera based on current index
    const targetDev = videoDevicesList[currentDeviceIndex % Math.max(1, videoDevicesList.length)];
    const videoConstraint = targetDev && targetDev.deviceId ? { deviceId: { exact: targetDev.deviceId } } : true;

    let stream = null;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraint });
    } catch (e) {
      console.warn("[Camera Constraint Fallback]: Unconstrained camera fallback");
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
    }

    video.srcObject = stream;
    await video.play();

    gesturesActive = true;
    btn.textContent = "GESTURES ON";
    btn.classList.add("active");

    processVideoFrameLoop();
  } catch (err) {
    console.error("Gesture camera initialization failed:", err);
    btn.textContent = "CAM ERROR";
    cameraBox.classList.remove("active");
  }
}

function stopGestures() {
  const cameraBox = document.getElementById("camera-box");
  const video = document.getElementById("webcam");
  const btn = document.getElementById("btn-gesture");

  gesturesActive = false;
  if (animFrameId) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }
  if (video && video.srcObject) {
    video.srcObject.getTracks().forEach(track => track.stop());
    video.srcObject = null;
  }
  if (handsInstance) {
    handsInstance.close();
    handsInstance = null;
  }

  cameraBox.classList.remove("active");
  btn.textContent = "GESTURES OFF";
  btn.classList.remove("active");
}

async function cycleCameraDevice() {
  if (videoDevicesList.length <= 1) {
    await refreshVideoDevicesList();
  }
  if (videoDevicesList.length > 0) {
    currentDeviceIndex = (currentDeviceIndex + 1) % videoDevicesList.length;
    console.log(`[🎥 Cycling to camera ${currentDeviceIndex}]:`, videoDevicesList[currentDeviceIndex].label);
    if (gesturesActive) {
      stopGestures();
      setTimeout(startGestures, 200);
    }
  }
}

function toggleGestures() {
  if (gesturesActive) {
    stopGestures();
  } else {
    startGestures();
  }
}
