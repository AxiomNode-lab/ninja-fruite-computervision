import { copyFile, mkdir, readdir, rm } from 'node:fs/promises';

// Produce a clean, static-only artifact for hosts such as Vercel.
// This intentionally excludes the Python desktop runtime and dependencies.
await rm('dist', { recursive: true, force: true });
await mkdir('dist/web', { recursive: true });
await mkdir('dist/vendor/mediapipe/wasm', { recursive: true });

for (const file of ['index.html', 'hand_landmarker.task']) {
  await copyFile(file, `dist/${file}`);
}

for (const file of ['app.js', 'core.js', 'art.js', 'style.css', 'tracker.worker.js']) {
  await copyFile(`web/${file}`, `dist/web/${file}`);
}

const mediapipeRoot = 'node_modules/@mediapipe/tasks-vision';
await copyFile(`${mediapipeRoot}/vision_bundle.mjs`, 'dist/vendor/mediapipe/vision_bundle.mjs');
for (const file of await readdir(`${mediapipeRoot}/wasm`)) {
  if (file.endsWith('.js') || file.endsWith('.wasm')) {
    await copyFile(`${mediapipeRoot}/wasm/${file}`, `dist/vendor/mediapipe/wasm/${file}`);
  }
}

console.log('Static browser game ready in dist/');
