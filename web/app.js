import { SmoothPoint, cameraPoint, intersects, splitFruit, difficultyAt } from './core.js';
import { drawFruit, drawBackground, fruits } from './art.js';

const $ = id => document.getElementById(id);
const canvas = $('game'), ctx = canvas.getContext('2d'), video = $('camera');
const STARTING_LIVES = 5, FRUIT_GRAVITY = 300, READY_SECONDS = 4;
let readyTime = READY_SECONDS, lastHandSeen = -Infinity;
let width = 1200, height = 620, mode = 'menu', input = 'pointer', paused = false;
let objects = [], pieces = [], drops = [], labels = [], trails = new Map();
let difficulty = difficultyAt(0), levelBanner = 0;
let score = 0, lives = STARTING_LIVES, combo = 0, lastSlice = 0, spawnTimer = .4, elapsed = 0;
let stream, worker, busy = false, cameraGeneration = 0, cameraReady = false, lastVideoTime = -1, lastInference = 0;
let requesting = false, pointerDown = false, flash = 0;
let best = 0;
try { best = Number(localStorage.getItem('fruit-ninja-best')) || 0; } catch { /* Storage is optional. */ }
$('best').textContent = best;

function status(text) { $('status').textContent = text; }
function resize() {
  const rect = canvas.getBoundingClientRect(); width = rect.width; height = rect.height;
  const dpr = Math.min(devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); trails.clear();
}
new ResizeObserver(resize).observe(canvas);
function hud() {
  $('score').textContent = String(score).padStart(3, '0');
  $('lives').textContent = '\u25cf '.repeat(Math.max(0, lives)) + '\u25cb '.repeat(STARTING_LIVES - Math.max(0, lives));
  $('lives').setAttribute('aria-label', `${lives} lives`);
  $('level').textContent = `LEVEL ${difficulty.level}`;
  $('level-detail').textContent = `${difficulty.speed.toFixed(2)}x speed` + (difficulty.nextIn === null ? ' / MAX' : ` / next in ${difficulty.nextIn}s`);
  $('combo').textContent = combo > 1 ? `${combo}× COMBO` : '';
}
function stopCamera() {
  cameraGeneration++; cameraReady = false; busy = false;
  stream?.getTracks().forEach(track => track.stop()); stream = null; video.srcObject = null;
  worker?.terminate(); worker = null; trails.clear();
  canvas.parentElement.classList.remove('show-camera'); $('preview').setAttribute('aria-pressed', 'false');
}
function begin(kind) {
  input = kind; mode = 'playing'; paused = false; pointerDown = false;
  objects = []; pieces = []; drops = []; labels = []; trails.clear();
  score = 0; lives = STARTING_LIVES; combo = 0; elapsed = 0; difficulty = difficultyAt(0); levelBanner = 0; spawnTimer = .35; readyTime = READY_SECONDS; lastHandSeen = -Infinity; hud();
  $('level-announcement').textContent = '';
  const showCamera = kind === 'camera';
  canvas.parentElement.classList.toggle('show-camera', showCamera);
  $('preview').setAttribute('aria-pressed', String(showCamera));
  $('preview').textContent = showCamera ? 'Hide camera' : 'Show camera';
  $('overlay').hidden = true; $('pause').hidden = false; $('exit').hidden = false;
  $('preview').hidden = kind !== 'camera'; $('pause').textContent = 'Pause';
  status(kind === 'camera' ? 'Raise your index finger to slice' : 'Drag to slice · mouse or touch');
}
function finish() {
  if (mode !== 'playing') return;
  mode = 'menu'; stopCamera();
  if (score > best) { best = score; try { localStorage.setItem('fruit-ninja-best', String(best)); } catch { /* Optional. */ } }
  $('best').textContent = best;
  $('title').textContent = `${score} points. Fresh work.`;
  $('description').textContent = 'Ready for another round? Five chances. Six levels. How far can you go?';
  $('start').textContent = 'Play with camera ↗'; $('overlay').hidden = false;
  for (const id of ['pause', 'exit', 'preview']) $(id).hidden = true;
  status('Round complete'); $('start').focus();
}

const cameraErrors = {
  NotAllowedError: 'Camera permission was denied. Allow camera access in your browser site settings, then try again.',
  NotFoundError: 'No camera found. Connect a camera, or play with mouse / touch.',
  NotReadableError: 'The camera is busy. Close other apps using it and try again.',
  SecurityError: 'Camera access is blocked by this browser or page. Open the site directly over HTTPS.',
};
async function startCamera() {
  if (requesting) return;
  requesting = true; $('start').disabled = true; $('start').textContent = 'Waiting for camera…';
  stopCamera(); const generation = cameraGeneration;
  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) throw new Error('Camera access needs HTTPS or localhost. You can still play with mouse / touch.');
    status('Allow camera access in your browser');
    const media = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } }, audio: false });
    if (generation !== cameraGeneration) { media.getTracks().forEach(t => t.stop()); return; }
    stream = media; video.srcObject = media; await video.play();
    if (generation !== cameraGeneration) return;
    status('Loading hand tracking…'); $('start').textContent = 'Preparing your blade…';
    // MediaPipe's WASM loader uses importScripts, so this must be a classic worker.
    worker = new Worker(new URL('./tracker.worker.js', import.meta.url));
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Hand tracking took too long to load. Check your connection and retry.')), 45000);
      worker.onerror = () => { clearTimeout(timeout); reject(new Error('Hand tracking could not load. Check your connection or try a current Chrome browser.')); };
      worker.onmessage = ({ data }) => {
        if (data.type === 'ready') { clearTimeout(timeout); resolve(); }
        else if (data.type === 'error') { clearTimeout(timeout); reject(new Error(data.message)); }
      };
      worker.postMessage({ type: 'init' });
    });
    if (generation !== cameraGeneration) return;
    worker.onmessage = ({ data }) => {
      busy = false;
      if (data.type === 'error') { trackingFailed(); return; }
      if (data.type === 'hands' && mode === 'playing' && !paused) receiveHands(data);
    };
    worker.onerror = trackingFailed;
    stream.getVideoTracks()[0].addEventListener('ended', trackingFailed);
    cameraReady = true; lastVideoTime = -1; begin('camera');
  } catch (error) {
    if (generation === cameraGeneration) {
      stopCamera(); $('description').textContent = cameraErrors[error.name] || error.message;
      status('Camera unavailable · mouse / touch is ready');
    }
  } finally {
    requesting = false; $('start').disabled = false; $('start').textContent = 'Enable camera & play ↗';
  }
}
function trackingFailed() {
  if (mode !== 'playing' || input !== 'camera') return;
  stopCamera(); input = 'pointer'; $('preview').hidden = true;
  status('Camera tracking stopped · drag with mouse / touch to continue');
}
function receiveHands(data) {
  // Discard late inference results instead of cutting at an outdated position.
  if (performance.now() - data.time > 150) { trails.clear(); return; }
  const active = new Set();
  data.landmarks.forEach((landmarks, i) => {
    const key = data.handedness[i]?.[0]?.categoryName || `hand-${i}`;
    if (active.has(key)) return; // Ambiguous handedness must not join unrelated hands.
    active.add(key);
    const point = cameraPoint(landmarks[8], video.videoWidth, video.videoHeight, width, height);
    moveBlade(key, point, data.time);
  });
  if (active.size) lastHandSeen = performance.now();
  for (const key of trails.keys()) if (!active.has(key)) trails.delete(key);
  status(active.size ? `${active.size === 2 ? 'Two hands' : 'Hand'} tracked · keep slicing` : 'Looking for your hand · step into the light');
}
async function capture(time) {
  if (!cameraReady || busy || paused || mode !== 'playing' || time - lastInference < 33 || video.readyState < 2 || video.currentTime === lastVideoTime) return;
  busy = true; lastInference = time; lastVideoTime = video.currentTime;
  const target = worker, generation = cameraGeneration;
  try {
    const bitmap = await createImageBitmap(video);
    if (generation !== cameraGeneration || target !== worker) { bitmap.close(); return; }
    target.postMessage({ type: 'frame', bitmap, time }, [bitmap]);
  } catch { if (generation === cameraGeneration) { busy = false; trackingFailed(); } }
}
function moveBlade(key, raw, time) {
  let trail = trails.get(key);
  if (!trail) { trail = { filter: new SmoothPoint(), points: [] }; trails.set(key, trail); }
  const point = trail.filter.update(raw, time), previous = trail.points.at(-1);
  if (point.reset) trail.points = [];
  trail.points.push({ ...point, time });
  trail.points = trail.points.filter(p => time - p.time < 180).slice(-24);
  if (!previous || point.reset || mode !== 'playing' || paused || readyTime > 0) return;
  const speed = Math.hypot(point.x - previous.x, point.y - previous.y) / Math.max(.001, (time - previous.time) / 1000);
  if (speed < 140) return;
  for (const fruit of objects) {
    if (fruit.hit || !intersects(previous, point, fruit)) continue;
    fruit.hit = true;
    if (fruit.kind === 'bomb') { lives--; score = Math.max(0, score - 30); combo = 0; flash = .2; splash(fruit, '#ffb55d', 30); }
    else {
      combo = elapsed - lastSlice < .65 ? combo + 1 : 1; lastSlice = elapsed;
      const points = 10 + Math.min(combo - 1, 8) * 5; score += points;
      const angle = Math.atan2(point.y - previous.y, point.x - previous.x) - fruit.rotation;
      pieces.push(...splitFruit(fruit, angle).map(piece => {
        // Split velocity uses world space, clipping uses fruit-local space.
        const world = angle + fruit.rotation + Math.PI / 2;
        piece.vx = fruit.vx + Math.cos(world) * piece.side * 155;
        piece.vy = fruit.vy * .3 + Math.sin(world) * piece.side * 155 - 65;
        return piece;
      }));
      splash(fruit, fruits[fruit.type].juice, 22);
      labels.push({ x: fruit.x, y: fruit.y, text: `+${points}`, age: 0 });
    }
    hud(); if (lives <= 0) { finish(); break; }
  }
}
function splash(fruit, color, count) {
  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2, speed = 65 + Math.random() * 260;
    drops.push({ x: fruit.x, y: fruit.y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed - 80, r: 2 + Math.random() * 5, age: 0, life: .45 + Math.random() * .4, color });
  }
}
function spawn() {
  const r = Math.max(23, Math.min(43, width * .044));
  const count = Math.random() < difficulty.doubleChance ? 2 : 1;
  for (let i = 0; i < count; i++) {
    const x = width * (.18 + Math.random() * .64);
    objects.push({ x, y: height + r, vx: (width / 2 - x) * .18, vy: -Math.sqrt(2 * FRUIT_GRAVITY * height * (.65 + Math.random() * .2)), r,
      rotation: Math.random() * .5 - .25, spin: Math.random() * 2 - 1, type: Math.floor(Math.random() * fruits.length), kind: elapsed > 12 && Math.random() < difficulty.bombChance ? 'bomb' : 'fruit' });
  }
}
function update(dt) {
  elapsed += dt;
  const nextDifficulty = difficultyAt(elapsed);
  if (nextDifficulty.level !== difficulty.level) {
    levelBanner = 2.5;
    $('level-announcement').textContent = `Level ${nextDifficulty.level}. Fruit speed increased.`;
  }
  difficulty = nextDifficulty;
  levelBanner = Math.max(0, levelBanner - dt);
  hud();
  spawnTimer -= dt;
  if (spawnTimer <= 0) { spawn(); spawnTimer = difficulty.spawnInterval + Math.random() * .2; }
  if (elapsed - lastSlice > .65 && combo) { combo = 0; hud(); }
  // Scale the physics clock to speed up the whole arc without changing its height.
  const motionDt = dt * difficulty.speed;
  for (const f of objects) {
    f.vy += FRUIT_GRAVITY * motionDt; f.x += f.vx * motionDt; f.y += f.vy * motionDt; f.rotation += f.spin * motionDt;
    if (!f.hit && f.y > height + f.r && f.vy > 0) {
      f.hit = true;
      if (f.kind !== 'bomb') { lives--; combo = 0; hud(); if (lives <= 0) { finish(); return; } }
    }
  }
  objects = objects.filter(f => !f.hit);
}
function render(time) {
  const dt = Math.min((time - (render.last || time)) / 1000, .033); render.last = time;
  const handVisible = input !== 'camera' || time - lastHandSeen < 400;
  if (mode === 'playing' && !paused) {
    void capture(time);
    // Give the player time to find the blade; freeze fruit when tracking is lost.
    if (handVisible) {
      if (readyTime > 0) readyTime = Math.max(0, readyTime - dt);
      else update(dt);
    }
  }
  drawBackground(ctx, width, height, time / 1000, canvas.parentElement.classList.contains('show-camera'));
  if (mode === 'menu') {
    const small = width < 650;
    const decor = [{ x: .16, y: .38, r: 60, type: 0 }, { x: .83, y: .34, r: 68, type: 1 }, { x: .12, y: .78, r: 45, type: 4 }, { x: .85, y: .79, r: 83, type: 2 }, { x: .68, y: .92, r: 29, type: 3 }];
    for (const [i, f] of decor.entries()) drawFruit(ctx, { ...f, x: f.x * width + (small ? (f.x < .5 ? -45 : 45) : 0), y: f.y * height + Math.sin(time / 1600 + i) * 9, r: f.r * (small ? .64 : 1), rotation: Math.sin(time / 2800 + i) * .2 });
  } else objects.forEach(f => drawFruit(ctx, f));
  const effectDt = paused || (mode === 'playing' && !handVisible) ? 0 : dt;
  for (const f of pieces) { f.age += effectDt; f.vy += 700 * effectDt; f.x += f.vx * effectDt; f.y += f.vy * effectDt; f.rotation += f.spin * effectDt; ctx.globalAlpha = Math.max(0, 1 - f.age / 1.1); drawFruit(ctx, f); }
  pieces = pieces.filter(f => f.age < 1.1); ctx.globalAlpha = 1;
  for (const p of drops) {
    p.age += effectDt; p.vy += 500 * effectDt; p.x += p.vx * effectDt; p.y += p.vy * effectDt;
    ctx.globalAlpha = Math.max(0, 1 - p.age / p.life); ctx.fillStyle = p.color;
    ctx.beginPath(); ctx.ellipse(p.x, p.y, p.r, p.r * .65, Math.atan2(p.vy, p.vx), 0, Math.PI * 2); ctx.fill();
  }
  drops = drops.filter(p => p.age < p.life); ctx.globalAlpha = 1;
  for (const label of labels) { label.age += effectDt; ctx.globalAlpha = Math.max(0, 1 - label.age); ctx.fillStyle = '#e5ffab'; ctx.font = 'bold 25px Outfit, sans-serif'; ctx.textAlign = 'center'; ctx.fillText(label.text, label.x, label.y - label.age * 70); }
  labels = labels.filter(p => p.age < 1); ctx.globalAlpha = 1;
  for (const trail of trails.values()) {
    const points = trail.points.filter(p => time - p.time < 180);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1], b = points[i], fade = Math.max(0, 1 - (time - b.time) / 180);
      ctx.globalAlpha = fade; ctx.strokeStyle = '#befe78'; ctx.shadowColor = '#befe78'; ctx.shadowBlur = 13; ctx.lineWidth = 2 + fade * 7;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      ctx.shadowBlur = 0; ctx.strokeStyle = '#f8ffe9'; ctx.lineWidth = 1 + fade * 2; ctx.stroke();
    }
    const p = trail.points.at(-1);
    if (p && time - p.time < 250) {
      ctx.globalAlpha = 1; ctx.shadowBlur = 0;
      ctx.beginPath(); ctx.arc(p.x, p.y, 17, 0, Math.PI * 2);
      ctx.fillStyle = '#10251b99'; ctx.fill();
      ctx.lineWidth = 3; ctx.strokeStyle = '#d2ff78'; ctx.stroke();
      ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff'; ctx.fill();
      ctx.beginPath(); ctx.moveTo(p.x - 24, p.y); ctx.lineTo(p.x - 12, p.y);
      ctx.moveTo(p.x + 12, p.y); ctx.lineTo(p.x + 24, p.y);
      ctx.moveTo(p.x, p.y - 24); ctx.lineTo(p.x, p.y - 12);
      ctx.moveTo(p.x, p.y + 12); ctx.lineTo(p.x, p.y + 24);
      ctx.lineWidth = 2; ctx.stroke();
    }
  }
  ctx.globalAlpha = 1; ctx.shadowBlur = 0;
  if (flash > 0) { flash -= effectDt; ctx.fillStyle = `rgba(255,116,65,${Math.max(0, flash)})`; ctx.fillRect(0, 0, width, height); }
  if (mode === 'playing' && levelBanner > 0 && !paused && handVisible) {
    ctx.fillStyle = '#14291ee6'; ctx.fillRect(width / 2 - 120, 110, 240, 44);
    ctx.fillStyle = '#d2ff78'; ctx.textAlign = 'center'; ctx.font = '500 20px Outfit, sans-serif';
    ctx.fillText(`LEVEL ${difficulty.level} - Speed up!`, width / 2, 138);
  }
  if (mode === 'playing' && !paused && (readyTime > 0 || !handVisible)) {
    ctx.fillStyle = '#10251bcc';
    const panelWidth = Math.min(width - 24, 420);
    ctx.fillRect((width - panelWidth) / 2, height / 2 - 55, panelWidth, 105);
    ctx.fillStyle = '#efffce'; ctx.textAlign = 'center';
    ctx.font = '500 25px Outfit, sans-serif';
    ctx.fillText(!handVisible ? 'Raise your index finger' : `Get ready... ${Math.ceil(readyTime)}`, width / 2, height / 2 - 12);
    ctx.font = '13px DM Sans, sans-serif';
    ctx.fillText(!handVisible ? 'Fruit waits until your hand is in view.' : 'The glowing ring is your blade.', width / 2, height / 2 + 20);
  }
  if (paused && mode === 'playing') { ctx.fillStyle = '#0b1818aa'; ctx.fillRect(0, 0, width, height); ctx.fillStyle = '#e8f4ce'; ctx.font = '500 36px Outfit, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('Take a breather.', width / 2, height / 2); }
  requestAnimationFrame(render);
}
function togglePause() { if (mode !== 'playing') return; paused = !paused; trails.clear(); pointerDown = false; $('pause').textContent = paused ? 'Resume' : 'Pause'; }
$('start').addEventListener('click', startCamera);
$('pointer').addEventListener('click', () => { stopCamera(); begin('pointer'); });
$('pause').addEventListener('click', togglePause);
$('exit').addEventListener('click', finish);
$('preview').addEventListener('click', () => { const shown = canvas.parentElement.classList.toggle('show-camera'); $('preview').setAttribute('aria-pressed', String(shown)); $('preview').textContent = shown ? 'Hide camera' : 'Show camera'; });
function pointer(event) { const rect = canvas.getBoundingClientRect(); moveBlade('pointer', { x: event.clientX - rect.left, y: event.clientY - rect.top }, performance.now()); }
canvas.addEventListener('pointerdown', event => { if (mode !== 'playing' || input !== 'pointer' || paused) return; pointerDown = true; trails.clear(); canvas.setPointerCapture(event.pointerId); pointer(event); });
canvas.addEventListener('pointermove', event => { if (pointerDown && input === 'pointer' && !paused) pointer(event); });
for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(name, () => { pointerDown = false; });
document.addEventListener('keydown', event => { if (event.code === 'Escape' && mode === 'playing') togglePause(); });
document.addEventListener('visibilitychange', () => { if (document.hidden && mode === 'playing' && !paused) togglePause(); });
window.addEventListener('pagehide', stopCamera);
requestAnimationFrame(render);
