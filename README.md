# Dälmönster · Knarkrondellen

A playable Three.js night scene based on the supplied Folkets Park photographs and gameplay reference. Custom Blender architecture, characters and props; original generated surface textures. No downloaded art assets.

## Play

```sh
npm install
npm run dev
```

Open the local URL printed by Vite. The game starts immediately.

- **WASD / arrows:** move relative to the camera.
- **Drag:** orbit the centered player, down to a 25° elevation. **Wheel:** zoom, within the closer 9–25 m camera range (14 m by default).
- **E:** talk to Big Black, continue the dialogue.
- **Shift:** jog; walking uses a slower, grounded pace. **R:** reset camera. **Esc:** close dialogue.
- **P:** display measured frame times and rendering statistics.

You arrive on the northwest street beside Hörnets Livs and can walk into the roundabout and its planted island. Planting, furniture, parked cars, buildings and the street boundary have collisions. Big Black is the only interactive NPC; two additional pedestrians stroll along street routes and pause when you stand in their way. The protagonist wears a hood and backpack, without a cat. The main mural says **LEGET BOIS**, with smaller original Möllan, Palestine and Gaza works along the wall. Big Black has a bald head and full beard modeled from the supplied portrait, with a slimmer torso and a taller, broader build than the player. He turns toward the player during dialogue. Low original Blender iron fences outline all three central beds and both curved border beds, matching the blocked planting areas.

The island follows `images/knarkrondellen3.png`: three separated central beds, wide connecting paths, curved planting strips beneath bare trees, and the grouped art columns on the open northern plaza. `src/layout.json` is shared by geometry generation, runtime placement, collisions and the lighting bake. Side streets, façades, park paths and empty parked cars extend beyond the playable boundary. The former Folkets Park gate has been removed and replaced by a continuous graffiti wall.

## Build and check

```sh
npm run build
npm run preview
npm test
```

Browser verification scripts use Playwright to connect to an existing local Chromium CDP endpoint recorded in `.dream-loop/browser-endpoint.txt`. `scripts/verify-browser.mjs` checks the real input/dialogue flow; `scripts/benchmark.mjs` measures idle and movement/orbit frame times at a native 1920×1080 drawing buffer. `scripts/capture.mjs` captures a fully loaded game view. `scripts/verify-island-update.mjs` checks all five fences, relative character dimensions and NPC dialogue facing from three approach directions, and captures the update.

## Assets and lighting

The editable Blender generation scripts are in `scripts/`. Run them with Blender 5.2 or a compatible version:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_environment.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_characters.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_props.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_planting.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_street_details.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_border_planting.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_pavers.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_leaf.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_surroundings.py -- --no-gate
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_streets.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_parked_car.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_parked_car_finish.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_facade_aprons.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_character_cloth.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_npc_proportions.py
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 3 --python scripts/build_characters_refined.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_island_fences.py
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 4 --python scripts/bake_environment_ao.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_environment_finish.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_environment_final.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_architecture_polish.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_architecture_weathered.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_cosy_street.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/finish_cosy_cloth.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_pedestrians.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_pavement_joins.py
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 3 --python scripts/build_arrival_setts.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_courtyard_edge.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_trees_polish.py
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 4 --python scripts/bake_lighting.py
```

Editable `.blend` files and working art reviews are in the ignored `.dream-loop/` folder. The runtime GLBs and textures are in `public/assets/`.

`scripts/build_road_fan.py` uses Python with NumPy, OpenCV and Shapely to trace our generated road texture into three original stone-mesh variants, then invokes Blender to export them. `scripts/bake_environment_ao.py` produces the derived architecture asset with corrected curved-wall normals and baked vertex contact shading; `scripts/build_environment_finish.py` adds window variation, curtain weave, stone tones and localized facade stains. `scripts/build_character_cloth.py` preserves the original character topology while adding shallow waist, elbow and hood folds.

Lighting uses a denoised 2048² Cycles diffuse irradiance bake, a static neighborhood environment capture, a restrained 768×432 planar reflection pass, cached environment shadows and a small moving character shadow map. The island uses instanced Blender stone meshes; lantern ironwork is merged by material. A small HDR bloom pass runs at quarter resolution, with restrained highlight glow. Wetness varies across stone faces and larger damp patches. There are no rain particles, volumetric passes, or screen-space ray-traced reflections. The performance target is **30 fps at 1080p on an Apple M1**. The base M1 render budget is capped at 1920×1080 pixels; other hardware can render up to 3200×1800 pixels. Hidden tabs stop rendering. Pause the game or close its test browser while baking to avoid resource contention.

Road and island stones use instancing, with conservative per-tile camera culling on the roadway. Cloth uses modeled folds and an original woven texture. The street extensions include raised sidewalk aprons, recessed entrances, empty parked cars and original asphalt grain.

The closest two apartment blocks are replaced by original curved ivory and ochre façades with salmon arched ground floors, recessed curtained windows, polygonal bays, turrets and tiled roofs. The arrival shop has a modeled interior, produce crates and a scalloped awning. Pavements connect to the building foundations, and four replacement trees have curved branch junctions and tapered bare twigs. The arrival street now has 3,681 individually fitted Blender granite setts with variable courses, staggered joints, unique texture samples, small repairs and a radial manhole collar. It uses a single draw call.

The player and all three NPCs use original Blender armatures with weighted knees, ankles and elbows. Cloth has more continuous tailoring and directional elbow folds. Runtime two-link leg IK keeps support feet at ground level while recovery feet lift; upper-body counter-rotation, head motion, relaxed elbows, backpack follow-through and damped start/stop blending replace the former rigid pendulum walk. Shift uses a faster gait with shorter ground-contact duration. There is no live cloth simulation or facial rig. Primary research and exact export details are recorded in `.dream-loop/character-techniques.md`; `scripts/verify-refinements.mjs` tests real camera dragging, all four rigs and actual planted-ankle heights.

## Measured performance

Latest local Chrome test on 2026-09-09, after character and arrival-street refinement: Apple M1, ANGLE Metal, native 1920×1080 drawing buffer, 30 fps cap. The 20-second arrival, 15-second island and 30-second movement/orbit/zoom samples each averaged **30.00 fps**. Movement p95 was **34.3 ms**, p99 **34.4 ms**, with **zero intervals over 50 ms** in all three samples. Mean CPU submission time was 5.86–7.53 ms; GPU timing was unavailable. These are actual local browser measurements, not a guarantee for every camera position or system load. Better hardware defaults to 60 fps and a larger pixel budget, but was not benchmarked here. See `.dream-loop/performance-refinements.json`.

The production build, **fourteen unit tests and seventeen general live browser checks pass**, along with the focused character, foot-contact and lower-camera checks. The live checks cover the new street spawn, two street pedestrians, gate removal, centered camera and zoom bounds, real keyboard/mouse movement, nearby Swedish dialogue, single reward, cat removal, boundaries and browser errors. Reports and captures are in `.dream-loop/performance-refinements.json`, `.dream-loop/browser-checks.json` and `.dream-loop/final-gameplay.png`.

The previous environment review, before the current character and arrival-street refinement, was **6.9/10, Tier 2**, below the concept's score-8 material-fidelity target. The hour improved the shop arrival, architecture, tree silhouettes, car materials and window depth, but bright window panels, some clean facade and awning surfaces, paving transitions and dark repeated curb faces remain visible limitations. See `.dream-loop/judge-hour-final.md` for the detailed review. This pass stayed within the authorized extra hour; the remaining visual gaps are recorded for later work.

The geographic reconstruction is an interpretation of the supplied photos, not a surveyed model. The current gameplay scope is a small exploration scene and one short Swedish dialogue.

## Hosting

The initial loading screen uses `images/loading.webp`. The interface has no footer, help panel or sound controls. Base M1 hardware defaults to a 30 fps cap; other hardware defaults to 60.

`npm run build` prepares `dist/` with only assets used by the game and verifies the 25 MiB per-file hosting limit. After rebuilding the large environment or architecture in Blender, run `python3 scripts/optimize-scene-textures.py` (requires Pillow) to regenerate the web versions. Their embedded textures use lossless WebP; geometry and decoded pixels are verified unchanged. The original Blender exports remain available in `public/assets/`.
