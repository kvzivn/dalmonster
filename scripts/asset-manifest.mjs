import { readFile, stat, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const root = resolve(import.meta.dirname, '..');
export async function getRuntimeAssets() {
  const source = await readFile(resolve(root, 'src/main.js'), 'utf8');
  const names = new Set([...source.matchAll(/["'`]\/assets\/([^"'`$]+)["'`]/g)].map(m => m[1]));
  for (const name of ['palestina', 'gaza', 'mollan']) names.add(`graffiti-${name}.png`);
  return names;
}
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const sizes = {};
  for (const name of await getRuntimeAssets()) sizes[`/assets/${name}`] = (await stat(resolve(root, 'public/assets', name))).size;
  await writeFile(resolve(root, 'src/asset-sizes.json'), JSON.stringify(sizes, null, 2) + '\n');
  console.log(`Loading manifest: ${Object.keys(sizes).length} assets`);
}
