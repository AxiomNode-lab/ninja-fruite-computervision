import test from 'node:test';
import assert from 'node:assert/strict';
import { SmoothPoint, intersects, cameraPoint, splitFruit, difficultyAt } from '../core.js';

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
test('tracking loss and position jumps reset instead of making phantom slices', () => {
  const filter = new SmoothPoint(); filter.update({ x: 0, y: 0 }, 1000);
  assert.equal(filter.update({ x: 100, y: 0 }, 1300).reset, true);
  assert.equal(filter.update({ x: 800, y: 0 }, 1333).reset, true);
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
