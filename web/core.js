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
  constructor() { this.point = null; this.time = 0; }
  update(point, time) {
    const dt = (time - this.time) / 1000;
    if (!this.point || dt > .15 || dt <= 0 || Math.hypot(point.x - this.point.x, point.y - this.point.y) > 330) {
      this.point = { ...point }; this.time = time;
      return { ...point, reset: true };
    }
    const speed = Math.hypot(point.x - this.point.x, point.y - this.point.y) / dt;
    // Adaptive low pass: steady at rest, responsive during a fast slice.
    const cutoff = 2.4 + .018 * speed;
    const alpha = 1 - Math.exp(-2 * Math.PI * cutoff * dt);
    this.point.x += alpha * (point.x - this.point.x);
    this.point.y += alpha * (point.y - this.point.y);
    this.time = time;
    return { ...this.point, reset: false };
  }
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
