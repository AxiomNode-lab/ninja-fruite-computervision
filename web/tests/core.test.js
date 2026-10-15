import test from 'node:test';
import assert from 'node:assert/strict';
import { SmoothPoint, acceptsTrackingResult, inferenceSize, intersects, cameraPoint, splitFruit, difficultyAt } from '../core.js';

test('levels advance at 20-second boundaries and restart at level one', () => {
  assert.equal(difficultyAt(19.99).level, 1);
  assert.equal(difficultyAt(20).level, 2);
  assert.equal(difficultyAt(40).level, 3);
  assert.equal(difficultyAt(0).speed, 1);
  assert.equal(difficultyAt(0).nextIn, 20);
});
test('successive levels increase speed and density with a playable upper limit', () => {
  for (let time = 20; time <= 100; time += 20) {
    const previous = difficultyAt(time - 20), next = difficultyAt(time);
    assert.ok(next.speed > previous.speed);
    assert.ok(next.spawnInterval < previous.spawnInterval);
    assert.ok(next.bombChance > previous.bombChance);
    assert.ok(next.doubleChance > previous.doubleChance);
  }
  assert.equal(difficultyAt(100).speed, 1.75);
  assert.deepEqual(difficultyAt(10000), difficultyAt(100));
  assert.equal(difficultyAt(100).nextIn, null);
});

test('fast swipes hit fruit between samples, not beyond segment endpoints', () => {
  assert.ok(intersects({ x: 0, y: 0 }, { x: 200, y: 0 }, { x: 100, y: 10, r: 20 }));
  assert.equal(intersects({ x: 0, y: 0 }, { x: 20, y: 0 }, { x: 100, y: 0, r: 20 }), false);
  assert.equal(intersects({ x: 0, y: 0 }, { x: 0, y: 0 }, { x: 100, y: 0, r: 20 }), false);
});
test('smoothing damps jitter and follows fast movement', () => {
  const filter = new SmoothPoint(); filter.update({ x: 100, y: 100 }, 1000);
  const jitter = filter.update({ x: 102, y: 100 }, 1033);
  assert.ok(jitter.x > 100 && jitter.x < 102);
  const swipe = filter.update({ x: 180, y: 100 }, 1066);
  assert.ok(swipe.x > 175);
});
test('latency compensation is bounded and leaves stationary input untouched', () => {
  const filter = new SmoothPoint(); filter.update({ x: 100, y: 100 }, 1000);
  const moving = filter.update({ x: 180, y: 100 }, 1033, 200);
  assert.ok(moving.x > 180);
  assert.ok(moving.x <= 250);

  const stationary = new SmoothPoint(); stationary.update({ x: 50, y: 50 }, 1000);
  assert.deepEqual(stationary.update({ x: 50, y: 50 }, 1033, 80), { x: 50, y: 50, reset: false });
});
test('inference frames preserve aspect ratio while capping their longest edge', () => {
  assert.deepEqual(inferenceSize(640, 480), { width: 480, height: 360 });
  assert.deepEqual(inferenceSize(480, 640), { width: 360, height: 480 });
  assert.deepEqual(inferenceSize(320, 240), { width: 320, height: 240 });
});
test('tracking loss and position jumps reset instead of making phantom slices', () => {
  const filter = new SmoothPoint(); filter.update({ x: 0, y: 0 }, 1000);
  assert.equal(filter.update({ x: 100, y: 0 }, 1600).reset, true);
  assert.equal(filter.update({ x: 800, y: 0 }, 1633).reset, true);
});
test('slow devices keep current tracking results without accepting abandoned work', () => {
  assert.equal(acceptsTrackingResult(150), true);
  assert.equal(acceptsTrackingResult(650), true);
  assert.equal(acceptsTrackingResult(2001), false);

  const filter = new SmoothPoint(); filter.update({ x: 0, y: 0 }, 1000);
  assert.equal(filter.update({ x: 50, y: 0 }, 1300).reset, false);
  assert.equal(filter.update({ x: 60, y: 0 }, 1900).reset, true);
});
test('One Euro filter resets when the same timestamp is reused', () => {
  const filter = new SmoothPoint(); filter.update({ x: 100, y: 100 }, 1000);
  const first = filter.update({ x: 104, y: 100 }, 1033);
  const repeated = filter.update({ x: 104, y: 100 }, 1033);
  assert.equal(repeated.reset, true);
  assert.equal(repeated.x, 104);
  assert.ok(first.x < repeated.x);
});
test('camera mapping mirrors and matches object-fit cover on portrait screens', () => {
  assert.deepEqual(cameraPoint({ x: .5, y: .5 }, 640, 480, 400, 600), { x: 200, y: 300 });
  assert.equal(cameraPoint({ x: .75, y: .5 }, 640, 480, 400, 600).x, 0);
});
test('slice produces complementary halves moving apart', () => {
  const source = { x: 10, y: 20, vx: 0, vy: -100, spin: 0 };
  const halves = splitFruit(source, 0);
  assert.equal(halves.length, 2);
  assert.equal(halves[0].side, -halves[1].side);
  assert.ok(halves[0].vy < halves[1].vy);
  assert.equal(source.side, undefined);
});
