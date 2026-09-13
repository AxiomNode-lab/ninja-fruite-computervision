export function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }

export function segmentCircleHit(x1, y1, x2, y2, cx, cy, radius) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len2 = dx * dx + dy * dy;
  if (len2 === 0) return Math.hypot(cx - x1, cy - y1) <= radius;
  const t = clamp(((cx - x1) * dx + (cy - y1) * dy) / len2, 0, 1);
  const px = x1 + t * dx;
  const py = y1 + t * dy;
  return Math.hypot(cx - px, cy - py) <= radius;
}

export function smoothPoint(previous, current, alpha = 0.48) {
  if (!previous) return { ...current };
  const a = clamp(alpha, 0, 1);
  return {
    x: previous.x + (current.x - previous.x) * a,
    y: previous.y + (current.y - previous.y) * a,
  };
}
