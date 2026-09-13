export const fruits = [
  { name: 'apple', light: '#ff9779', color: '#ee473f', dark: '#8c192d', flesh: '#fff0bb', juice: '#ff6e59' },
  { name: 'orange', light: '#ffe18a', color: '#ff9d25', dark: '#d75114', flesh: '#ffbf52', juice: '#ffb940' },
  { name: 'watermelon', light: '#a5d865', color: '#3c9b55', dark: '#15583b', flesh: '#fb5861', juice: '#ff6376' },
  { name: 'lemon', light: '#fffbb0', color: '#f2d446', dark: '#b99216', flesh: '#fff19b', juice: '#f5e963' },
  { name: 'plum', light: '#d6a3f7', color: '#9966be', dark: '#482d72', flesh: '#ffce77', juice: '#cda1eb' },
];
const TAU = Math.PI * 2;
function ellipse(ctx, x, y, rx, ry, color, rotation = 0) {
  ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rotation, 0, TAU); ctx.fillStyle = color; ctx.fill();
}
function body(ctx, type) {
  ctx.beginPath();
  if (type === 'apple') {
    ctx.moveTo(0, -.78); ctx.bezierCurveTo(-.9, -1.3, -1.2, -.35, -.85, .4);
    ctx.bezierCurveTo(-.55, 1.1, -.25, 1, 0, .86); ctx.bezierCurveTo(.5, 1.18, .83, .7, .98, .05);
    ctx.bezierCurveTo(1.12, -.65, .6, -1.18, 0, -.78);
  } else ctx.ellipse(0, 0, type === 'lemon' ? 1.13 : 1, type === 'plum' ? 1.08 : .96, 0, 0, TAU);
  ctx.closePath();
}
export function drawFruit(ctx, f) {
  ctx.save(); ctx.translate(f.x, f.y); ctx.rotate(f.rotation || 0); ctx.scale(f.r, f.r);
  if (f.kind === 'bomb') {
    const g = ctx.createRadialGradient(-.35, -.4, .05, 0, 0, 1); g.addColorStop(0, '#7c8680'); g.addColorStop(.4, '#333e3a'); g.addColorStop(1, '#111816');
    ellipse(ctx, 0, 0, .94, .94, g); ctx.strokeStyle = '#a1a78b'; ctx.lineWidth = .09;
    ctx.beginPath(); ctx.moveTo(.05, -.85); ctx.quadraticCurveTo(.08, -1.4, .5, -1.2); ctx.stroke();
    ellipse(ctx, .5, -1.2, .13, .13, '#ffd66d');
    ctx.strokeStyle = '#ffbd60'; ctx.lineWidth = .035;
    for (let i = 0; i < 8; i++) { const a = i * TAU / 8; ctx.beginPath(); ctx.moveTo(.5 + Math.cos(a) * .18, -1.2 + Math.sin(a) * .18); ctx.lineTo(.5 + Math.cos(a) * .3, -1.2 + Math.sin(a) * .3); ctx.stroke(); }
    ctx.strokeStyle = '#f29974'; ctx.lineWidth = .08; ctx.beginPath(); ctx.moveTo(-.2, -.2); ctx.lineTo(.2, .2); ctx.moveTo(.2, -.2); ctx.lineTo(-.2, .2); ctx.stroke(); ctx.restore(); return;
  }
  const palette = fruits[f.type];
  if (f.side) {
    // Clip the fruit into two complementary halves in the original cut direction.
    ctx.rotate(f.cut); ctx.beginPath(); ctx.rect(-2, f.side > 0 ? 0 : -2, 4, 2); ctx.clip(); ctx.rotate(-f.cut);
  }
  ctx.shadowColor = '#0005'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 7;
  const gradient = ctx.createRadialGradient(-.4, -.45, .08, .15, .25, 1.2);
  gradient.addColorStop(0, palette.light); gradient.addColorStop(.42, palette.color); gradient.addColorStop(1, palette.dark);
  body(ctx, palette.name); ctx.fillStyle = gradient; ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.save(); body(ctx, palette.name); ctx.clip();
  if (palette.name === 'watermelon') {
    ctx.strokeStyle = '#194e3977'; ctx.lineWidth = .12;
    for (let x = -.8; x <= .9; x += .35) { ctx.beginPath(); ctx.moveTo(x, -1); ctx.bezierCurveTo(x - .25, -.3, x + .3, .3, x, 1); ctx.stroke(); }
  } else if (palette.name === 'orange' || palette.name === 'lemon') {
    for (let i = 0; i < 70; i++) { const a = i * 2.39996, r = Math.sqrt(i / 70) * .94; ellipse(ctx, Math.cos(a) * r, Math.sin(a) * r, .018, .014, '#fff4bc33'); }
  }
  ellipse(ctx, -.35, -.48, .25, .12, '#ffffff45', -.65); ctx.restore();
  if (f.side) {
    ctx.rotate(f.cut); ellipse(ctx, 0, 0, .91, .22, palette.flesh);
    ctx.strokeStyle = '#fff7cb80'; ctx.lineWidth = .025;
    if (['orange', 'lemon'].includes(palette.name)) {
      for (let i = 0; i < 10; i++) { const a = TAU * i / 10; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * .85, Math.sin(a) * .19); ctx.stroke(); }
    } else { for (const x of [-.55, -.25, .25, .55]) ellipse(ctx, x, f.side * .06, .035, .06, '#603236', .4); }
  } else {
    ctx.strokeStyle = '#816043'; ctx.lineWidth = .09; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(0, -.79); ctx.quadraticCurveTo(.03, -1.01, -.07, -1.14); ctx.stroke();
    ellipse(ctx, .24, -.99, .3, .12, '#74b85b', -.35);
    ctx.strokeStyle = '#c4dc8055'; ctx.lineWidth = .02; ctx.beginPath(); ctx.moveTo(.03, -.93); ctx.lineTo(.45, -1.06); ctx.stroke();
  }
  ctx.restore();
}

export function drawBackground(ctx, w, h, time, preview) {
  ctx.clearRect(0, 0, w, h);
  const g = ctx.createRadialGradient(w * .48, h * .42, 0, w * .5, h * .5, w * .75);
  g.addColorStop(0, preview ? '#24382a14' : '#2a3e2c'); g.addColorStop(1, preview ? '#101e1840' : '#101f1b');
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = '#b3d78a07'; ctx.lineWidth = 1;
  for (let x = 0; x < w; x += 65) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
  for (let y = 0; y < h; y += 65) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  for (let i = 0; i < 22; i++) ellipse(ctx, (i * 137.2) % w, (i * 97.4 - time * 5 % h + h) % h, 1.5, 1.5, '#d3eba320');
}
