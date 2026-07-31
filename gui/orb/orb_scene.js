(function() {
  const container = document.getElementById("orb-container");
  const width = container.clientWidth || window.innerWidth;
  const height = container.clientHeight || window.innerHeight;

  // --- PERFORMANCE MODE STATE ---
  let lowPowerMode = true; // Default to Low-Power Mode for Intel HD Graphics compatibility

  // --- SCENE & CAMERA ---
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 500);
  const HOME_POSITION = new THREE.Vector3(0, 0.4, 5.5);
  camera.position.copy(HOME_POSITION);

  const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(lowPowerMode ? 1.0 : Math.min(window.devicePixelRatio, 1.5)); // Default high resolution for Ultra Bloom
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  container.appendChild(renderer.domElement);

  // --- POST-PROCESSING (UNREAL BLOOM) ---
  const composer = new THREE.EffectComposer(renderer);
  composer.addPass(new THREE.RenderPass(scene, camera));

  const bloomPass = new THREE.UnrealBloomPass(
    new THREE.Vector2(width, height),
    1.4,  // strength
    0.35, // radius
    0.2   // threshold
  );
  composer.addPass(bloomPass);

  // --- ORBIT CONTROLS ---
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 0.6;
  controls.maxDistance = 35;
  controls.zoomSpeed = 1.4;
  controls.enablePan = false;

  // --- COLOR PALETTE ---
  const C_BRIGHT = 0x00f0ff;
  const C_MID    = 0x0088ff;
  const C_DIM    = 0x0044aa;
  const C_FAINT  = 0x002255;
  const C_HOT    = 0xffffff;

  const orbGroup = new THREE.Group();
  scene.add(orbGroup);

  function lineMat(color, opacity = 1) {
    return new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
  }

  function latRing(radius, lat, segs = 80) {
    const r = radius * Math.cos(lat);
    const y = radius * Math.sin(lat);
    const pts = [];
    for (let i = 0; i <= segs; i++) {
      const a = (i / segs) * Math.PI * 2;
      pts.push(new THREE.Vector3(r * Math.cos(a), y, r * Math.sin(a)));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }

  function meridian(radius, lon, segs = 80) {
    const pts = [];
    for (let i = 0; i <= segs; i++) {
      const lat = (i / segs) * Math.PI - Math.PI / 2;
      pts.push(new THREE.Vector3(
        radius * Math.cos(lat) * Math.cos(lon),
        radius * Math.sin(lat),
        radius * Math.cos(lat) * Math.sin(lon)
      ));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }

  // --- LAYER 1: OUTER SHELL ---
  const outerShell = new THREE.Group();
  const R1 = 2.0;

  for (let i = -12; i <= 12; i++) {
    const lat = (i / 12) * (Math.PI / 2) * 0.95;
    const opacity = i % 3 === 0 ? 0.6 : 0.18;
    const color = i % 3 === 0 ? C_MID : C_FAINT;
    outerShell.add(new THREE.Line(latRing(R1, lat), lineMat(color, opacity)));
  }

  for (let i = 0; i < 18; i++) {
    const lon = (i / 18) * Math.PI * 2;
    const isMajor = i % 6 === 0;
    outerShell.add(new THREE.Line(meridian(R1, lon), lineMat(isMajor ? C_BRIGHT : C_FAINT, isMajor ? 0.65 : 0.15)));
  }

  // Equator Bright Band
  for (let j = 0; j < 12; j++) {
    const t = (j / 11) * 2 - 1;
    const offset = (t * 0.35) / 2;
    const opacity = 0.85 * (1 - Math.abs(t) * 0.6);
    const color = Math.abs(t) < 0.3 ? C_BRIGHT : C_MID;
    outerShell.add(new THREE.Line(latRing(R1, offset, 120), lineMat(color, opacity)));
  }
  orbGroup.add(outerShell);

  // --- LAYER 2: SECONDARY ARCS ---
  const shell2 = new THREE.Group();
  const R2 = 2.12;

  for (let i = 0; i < 10; i++) {
    const lat = (Math.random() - 0.5) * Math.PI * 0.85;
    const startLon = Math.random() * Math.PI * 2;
    const arcLen = 0.4 + Math.random() * 1.2;
    const pts = [];
    const r = R2 * Math.cos(lat);
    const y = R2 * Math.sin(lat);
    for (let j = 0; j <= 30; j++) {
      const a = startLon + (j / 30) * arcLen;
      pts.push(new THREE.Vector3(r * Math.cos(a), y, r * Math.sin(a)));
    }
    shell2.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), lineMat(C_BRIGHT, 0.4)));
  }
  orbGroup.add(shell2);

  // --- LAYER 3: INNER CORE ---
  const innerCore = new THREE.Group();
  const R3 = 0.9;

  for (let s = 0; s < 6; s++) {
    const pts = [];
    const turns = 3;
    const phase = (s / 6) * Math.PI * 2;
    for (let i = 0; i <= 120; i++) {
      const t = i / 120;
      const lat = t * Math.PI - Math.PI / 2;
      const lon = t * turns * Math.PI * 2 + phase;
      pts.push(new THREE.Vector3(
        R3 * Math.cos(lat) * Math.cos(lon),
        R3 * Math.sin(lat),
        R3 * Math.cos(lat) * Math.sin(lon)
      ));
    }
    innerCore.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), lineMat(C_BRIGHT, 0.45)));
  }
  orbGroup.add(innerCore);

  // --- LAYER 4: HOT CORE ---
  const icoGeo = new THREE.IcosahedronGeometry(0.25, 1);
  const icoEdges = new THREE.EdgesGeometry(icoGeo);
  const icoWire = new THREE.LineSegments(icoEdges, lineMat(C_HOT, 0.95));
  orbGroup.add(icoWire);

  const coreSphereMat = new THREE.MeshBasicMaterial({
    color: C_BRIGHT,
    transparent: true,
    opacity: 0.25,
    blending: THREE.AdditiveBlending
  });
  const coreSphere = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 12), coreSphereMat);
  orbGroup.add(coreSphere);

  // --- SATELLITES & DEBRIS ---
  const debris = [];
  const debrisGeos = [
    new THREE.IcosahedronGeometry(0.015, 0),
    new THREE.IcosahedronGeometry(0.025, 0),
    new THREE.TetrahedronGeometry(0.02, 0)
  ];

  for (let i = 0; i < 90; i++) {
    const geo = debrisGeos[Math.floor(Math.random() * debrisGeos.length)];
    const mat = new THREE.MeshBasicMaterial({
      color: Math.random() > 0.6 ? C_BRIGHT : C_MID,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending
    });
    const mesh = new THREE.Mesh(geo, mat);
    const orbitR = 1.3 + Math.random() * 3.5;
    const speed = (0.08 + Math.random() * 0.4) * (Math.random() > 0.5 ? 1 : -1);
    const tiltX = (Math.random() - 0.5) * Math.PI * 0.8;
    const tiltZ = (Math.random() - 0.5) * Math.PI * 0.5;
    const phase = Math.random() * Math.PI * 2;
    mesh.userData = { orbitR, speed, tiltX, tiltZ, phase };
    debris.push(mesh);
    orbGroup.add(mesh);
  }

  // --- DUST PARTICLES ---
  const dustCount = 600;
  const dustPos = new Float32Array(dustCount * 3);
  for (let i = 0; i < dustCount; i++) {
    const rr = 0.5 + Math.pow(Math.random(), 0.6) * 6.0;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    dustPos[i * 3]     = rr * Math.sin(phi) * Math.cos(theta);
    dustPos[i * 3 + 1] = rr * Math.cos(phi);
    dustPos[i * 3 + 2] = rr * Math.sin(phi) * Math.sin(theta);
  }
  const dustGeo = new THREE.BufferGeometry();
  dustGeo.setAttribute('position', new THREE.Float32BufferAttribute(dustPos, 3));
  const dustMat = new THREE.PointsMaterial({
    size: 0.04,
    transparent: true,
    opacity: 0.55,
    blending: THREE.AdditiveBlending,
    color: C_BRIGHT
  });
  const dustPoints = new THREE.Points(dustGeo, dustMat);
  orbGroup.add(dustPoints);

  // --- SCAN RINGS ---
  function makeScanRing(radius) {
    const geo = new THREE.RingGeometry(radius - 0.015, radius + 0.015, 80);
    const mat = new THREE.MeshBasicMaterial({
      color: C_BRIGHT,
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = Math.PI / 2;
    return mesh;
  }
  const scanRing1 = makeScanRing(R1);
  orbGroup.add(scanRing1);

  // --- CAMERA API FOR GESTURES & BUTTONS ---
  const sphericalScratch = new THREE.Spherical();
  const offsetScratch = new THREE.Vector3();

  function rotateBy(deltaTheta, deltaPhi) {
    offsetScratch.copy(camera.position).sub(controls.target);
    sphericalScratch.setFromVector3(offsetScratch);
    sphericalScratch.theta -= deltaTheta;
    sphericalScratch.phi = Math.max(0.05, Math.min(Math.PI - 0.05, sphericalScratch.phi - deltaPhi));
    sphericalScratch.makeSafe();
    offsetScratch.setFromSpherical(sphericalScratch);
    camera.position.copy(controls.target).add(offsetScratch);
    camera.lookAt(controls.target);
  }

  function zoomBy(factor) {
    offsetScratch.copy(camera.position).sub(controls.target);
    const dist = Math.max(0.6, Math.min(35, offsetScratch.length() * factor));
    offsetScratch.setLength(dist);
    camera.position.copy(controls.target).add(offsetScratch);
  }

  function resetView() {
    camera.position.copy(HOME_POSITION);
    controls.target.set(0, 0, 0);
    camera.lookAt(controls.target);
    controls.update();
  }

  function togglePerformanceMode() {
    lowPowerMode = !lowPowerMode;
    const btn = document.getElementById("btn-perf");
    if (lowPowerMode) {
      renderer.setPixelRatio(1.0);
      btn.textContent = "iGPU MODE: LOW-POWER";
      btn.classList.add("active");
    } else {
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      btn.textContent = "iGPU MODE: ULTRA BLOOM";
      btn.classList.remove("active");
    }
    return lowPowerMode;
  }

  window.orbApi = {
    rotateBy,
    zoomBy,
    zoomIn: () => zoomBy(0.85),
    zoomOut: () => zoomBy(1.18),
    resetView,
    togglePerformanceMode
  };

  // --- ANIMATION LOOP ---
  const clock = new THREE.Clock();
  let renderPaused = false;

  function animate() {
    if (renderPaused) return; // Exit render loop entirely!
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    outerShell.rotation.y += 0.0015;
    shell2.rotation.y -= 0.0012;
    innerCore.rotation.y -= 0.005;
    icoWire.rotation.x += 0.008;
    icoWire.rotation.y += 0.012;

    const surge = Math.pow(Math.max(0, Math.sin(t * 1.5)), 4) * 0.8;
    coreSphere.scale.setScalar(1 + surge);
    coreSphereMat.opacity = 0.25 + surge * 0.4;

    debris.forEach((d) => {
      const u = d.userData;
      const a = t * u.speed + u.phase;
      d.position.set(
        u.orbitR * Math.cos(a) * Math.cos(u.tiltX),
        u.orbitR * Math.sin(u.tiltX) * Math.sin(a * 0.8) + Math.sin(a * 0.3 + u.tiltZ) * 0.2,
        u.orbitR * Math.sin(a) * Math.cos(u.tiltZ)
      );
      d.rotation.x += 0.015;
    });

    const scanY = Math.sin(t * 0.4) * R1;
    scanRing1.position.y = scanY;
    const scanS = Math.sqrt(Math.max(0, R1 * R1 - scanY * scanY)) / R1;
    scanRing1.scale.set(scanS, scanS, 1);

    controls.update();

    if (lowPowerMode) {
      // Direct WebGL render for 0 GPU lag on Intel HD 4400!
      renderer.render(scene, camera);
    } else {
      // Full Unreal Bloom Post-Processing Pass
      composer.render();
    }
  }

  // Poll status endpoint every 500ms
  setInterval(async () => {
    try {
      const response = await fetch('/status');
      const data = await response.json();
      if (data.paused !== renderPaused) {
        renderPaused = data.paused;
        if (!renderPaused) {
          // Re-trigger animate loop
          animate();
          console.log("J.A.R.V.I.S. Orb Render Loop Resumed.");
        } else {
          console.log("J.A.R.V.I.S. Orb Render Loop Suspended.");
        }
      }
    } catch (e) {
      // Ignore network errors
    }
  }, 500);

  animate();

  window.addEventListener('resize', () => {
    const w = container.clientWidth || window.innerWidth;
    const h = container.clientHeight || window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
  });
})();
