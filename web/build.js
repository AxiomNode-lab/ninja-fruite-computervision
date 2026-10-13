import { copyFile, mkdir, rm } from 'node:fs/promises';

// Produce a clean, static-only artifact for hosts such as Vercel.
// This intentionally excludes the Python desktop runtime and dependencies.
await rm('dist', { recursive: true, force: true });
await mkdir('dist/web', { recursive: true });

for (const file of ['index.html', 'hand_landmarker.task']) {
  await copyFile(file, `dist/${file}`);
}

for (const file of ['app.js', 'core.js', 'art.js', 'style.css', 'tracker.worker.js']) {
  await copyFile(`web/${file}`, `dist/web/${file}`);
}

console.log('Static browser game ready in dist/');
