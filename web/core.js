// Shared deterministic motion and collision math; independent of the DOM.
export function difficultyAt(elapsed) {
  const level = Math.min(6, Math.floor(Math.max(0, elapsed) / 20) + 1);
  return {
    level,
    speed: 1 + (level - 1) * .15,
    spawnInterval: 1.5 - (level - 1) * .12,
    doubleChance: .2 + (level - 1) * .06,
    bombChance: .08 + (level - 1) * .02,
    nextIn: level < 6 ? Math.ceil(level * 20 - elapsed) : null,
  };
}

export function intersects(a, b, fruit, padding = 5) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const length = dx * dx + dy * dy;
  const t = length ? Math.max(0, Math.min(1, ((fruit.x - a.x) * dx + (fruit.y - a.y) * dy) / length)) : 0;
  return Math.hypot(fruit.x - a.x - t * dx, fruit.y - a.y - t * dy) <= fruit.r + padding;
}

export class SmoothPoint {
  constructor() {
    this.point = null; this.raw = null; this.time = 0;
    this.derivative = { x: 0, y: 0 };
  }
  update(point, time) {
    const dt = (time - this.time) / 1000;
    if (!this.point || dt > .15 || dt <= 0 || Math.hypot(point.x - this.raw.x, point.y - this.raw.y) > 330) {
      this.point = { ...point }; this.raw = { ...point }; this.time = time;
      this.derivative = { x: 0, y: 0 };
      return { ...point, reset: true };
    }
    // Canonical One Euro filter: smooth the derivative, then use motion speed
    // to reduce smoothing during deliberate fast swipes.
    const derivativeAlpha = oneEuroAlpha(1, dt);
    this.derivative.x += derivativeAlpha * ((point.x - this.raw.x) / dt - this.derivative.x);
    this.derivative.y += derivativeAlpha * ((point.y - this.raw.y) / dt - this.derivative.y);
    const cutoff = 1.7 + .22 * Math.hypot(this.derivative.x, this.derivative.y);
    const alpha = oneEuroAlpha(cutoff, dt);
    this.point.x += alpha * (point.x - this.point.x);
    this.point.y += alpha * (point.y - this.point.y);
    this.raw = { ...point }; this.time = time;
    return { ...this.point, reset: false };
  }
}

function oneEuroAlpha(cutoff, dt) {
  const tau = 1 / (2 * Math.PI * cutoff);
  return 1 / (1 + tau / dt);
}

export function cameraPoint(point, videoWidth, videoHeight, width, height) {
  const scale = Math.max(width / videoWidth, height / videoHeight);
  return { x: (1 - point.x) * videoWidth * scale - (videoWidth * scale - width) / 2,
    y: point.y * videoHeight * scale - (videoHeight * scale - height) / 2 };
}

export function splitFruit(fruit, angle) {
  return [-1, 1].map(side => ({ ...fruit, side, cut: angle, age: 0,
    vx: fruit.vx + Math.cos(angle + Math.PI / 2) * side * 155,
    vy: fruit.vy * .3 + Math.sin(angle + Math.PI / 2) * side * 155 - 65,
    spin: side * (1.8 + Math.abs(fruit.spin || 0)) }));
}
