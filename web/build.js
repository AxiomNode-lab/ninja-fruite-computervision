import { mkdir, copyFile } from 'node:fs/promises';
// An explicit allowlist keeps the Python environment and repository files private.
await mkdir('dist/web', { recursive: true });
for (const file of ['index.html', 'hand_landmarker.task']) await copyFile(file, `dist/${file}`);
for (const file of ['app.js', 'core.js', 'art.js', 'style.css', 'tracker.worker.js']) await copyFile(`web/${file}`, `dist/web/${file}`);
console.log('Static game ready in dist/');
