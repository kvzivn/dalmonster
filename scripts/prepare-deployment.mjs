import { getRuntimeAssets } from './asset-manifest.mjs';
// Keep original Blender exports in source control, but publish only runtime assets.
import { readFile, readdir, rm, stat } from 'node:fs/promises';
import { resolve } from 'node:path';
const root = resolve(import.meta.dirname, '..');
const required = await getRuntimeAssets();
for (const name of required) {
  const file = resolve(root, 'dist/assets', name);
  if (!(await stat(file)).isFile()) throw new Error(`Missing runtime asset: ${name}`);
}
let removed = 0;
for (const name of await readdir(resolve(root, 'public/assets'))) {
  if (!required.has(name)) {
    await rm(resolve(root, 'dist/assets', name), { recursive: true, force: true });
    removed++;
  }
}
let bytes = 0;
for (const name of await readdir(resolve(root, 'dist/assets'))) {
  const size = (await stat(resolve(root, 'dist/assets', name))).size;
  if (size > 25 * 1024 * 1024) throw new Error(`Asset exceeds hosting limit: ${name}`);
  bytes += size;
}
const html = await readFile(resolve(root, 'dist/index.html'), 'utf8');
const loading = html.match(/<img src="([^\"]+\.webp)"/);
if (!loading) throw new Error('Loading artwork missing from built HTML');
await stat(resolve(root, 'dist', loading[1].replace(/^\//, '')));
if (/(?:id="(?:controls|help|sound|help-panel|frame-rate)")/.test(html)) throw new Error('Removed footer UI returned');
console.log(`Deployment ready: ${required.size} runtime assets; ${removed} source-only assets omitted; ${(bytes / 1024 / 1024).toFixed(1)} MiB total.`);
