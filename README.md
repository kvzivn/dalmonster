<p align="center">
  <img width="600" alt="Dalmonster" src="https://github.com/user-attachments/assets/8fb86640-3af3-4e89-8296-f96c2ef0a8b6" />
</p>

<p align="center">
  A single-player RPG set on the streets of Malmö.
</p>

## Play

```sh
npm install
npm run dev
```

Open the local URL printed by Vite. Explore the neighbourhood and talk to Big Black in a short Swedish dialogue.

* **WASD / arrows:** move
* **Drag / wheel:** orbit / zoom
* **Shift:** jog
* **E:** talk / continue dialogue
* **Esc:** close dialogue
* **R:** reset camera
* **P:** performance statistics

## Development

```sh
npm run build    # Production build → dist/
npm run preview  # Preview locally
npm test         # Unit tests
```

* `src/layout.json` — shared scene layout, collisions and lighting placement.
* `scripts/` — Blender asset generation, lighting bakes and browser checks.
* `public/assets/` — runtime models and textures.

Browser checks use Playwright with a local Chromium CDP endpoint recorded in `.dream-loop/browser-endpoint.txt`.

## Performance & hosting

Targets **30 fps at 1080p on Apple M1**, achieved in local browser tests. Other hardware defaults to a 60 fps cap but has not been benchmarked.

Hosted at [dalmonster.vercel.app](https://dalmonster.vercel.app) on Vercel. Pushes to `main` build and deploy automatically. The game is public and does not require an account.

The loading screen shows a white, byte-weighted progress bar beneath the artwork’s loading text.

The production output is `dist/`. The build includes only used assets and checks a portable **25 MiB per-file asset budget**. After rebuilding large environment assets, run `python3 scripts/optimize-scene-textures.py` (requires Pillow) before building.
