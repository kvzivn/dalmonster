import { CAMERA, SPAWN } from "../src/neighbourhood.js";
import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import assert from "node:assert/strict";
const endpoint = (
  await fs.readFile(".dream-loop/browser-endpoint.txt", "utf8")
).trim();
const browser = await chromium.connectOverCDP(endpoint);
const page = browser
  .contexts()[0]
  .pages()
  .find((p) => p.url().includes("5173"));
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.reload();
await page.waitForFunction(() => window.__game?.ready);
await page.waitForTimeout(1000);
const checks = [];
const initial=await page.evaluate(()=>__game.state);
assert(Math.abs(initial.position[0]-SPAWN.x)<.001 && Math.abs(initial.position[2]-SPAWN.z)<.001);
checks.push({test:"Player starts on the northwest street"});
const walkers=await page.evaluate(()=>__game.pedestrians.map(s=>({name:s.root.name,interactive:s.root.userData.interactive,p:s.root.position.toArray()})));
assert.equal(walkers.length,2);assert(walkers.every(s=>s.interactive===false));
await page.waitForTimeout(3000);
const walkersAfter=await page.evaluate(()=>__game.pedestrians.map(s=>s.root.position.toArray()));
assert(walkers.every((s,i)=>Math.hypot(s.p[0]-walkersAfter[i][0],s.p[2]-walkersAfter[i][2])>.4));
checks.push({test:"Exactly two non-interactive pedestrians walk on street routes"});
assert(await page.evaluate(()=>{let found=false;__game.scene.traverse(o=>{if(o.name.startsWith('Park_Gate'))found=true;});return !found&&!!__game.scene.getObjectByName('Hero_LEGET_BOIS');}));
checks.push({test:"Park entrance removed and main graffiti retained"});
const state = () => page.evaluate(() => window.__game.state);
// Isolated road position supplies room to test camera-relative controls without planting interference.
assert(await page.evaluate(() => window.__game.teleport(0, 17)));
let before = await state();
await page.keyboard.down("w");
await page.waitForTimeout(700);
await page.keyboard.up("w");
let after = await state();
const dx = after.position[0] - before.position[0],
  dz = after.position[2] - before.position[2];
assert(dx * -Math.sin(CAMERA.yaw) + dz * -Math.cos(CAMERA.yaw) > .8);
checks.push({ test: "W follows camera heading", distance: Math.hypot(dx, dz) });
await page.keyboard.down("ArrowDown");
await page.waitForTimeout(700);
await page.keyboard.up("ArrowDown");
after = await state();
assert(
  Math.hypot(
    after.position[0] - before.position[0],
    after.position[2] - before.position[2],
  ) < 0.3,
);
checks.push({ test: "ArrowDown reverses W" });
const oldYaw = after.yaw;
await page.mouse.move(900, 600);
await page.mouse.down();
await page.mouse.move(1150, 620, { steps: 12 });
await page.mouse.up();
await page.waitForTimeout(600);
after = await state();
assert(Math.abs(after.yaw - oldYaw) > 1);
checks.push({ test: "Mouse drag orbits" });
const oldDistance = after.distance;
await page.mouse.wheel(0, -450);
await page.waitForTimeout(700);
after = await state();
assert(after.distance < oldDistance - 3);
checks.push({ test: "Wheel zooms" });
await page.keyboard.press("r");
await page.waitForTimeout(700);
assert(Math.abs((await state()).distance - CAMERA.distance) < 0.1);
checks.push({ test: "R resets view" });
await page.mouse.wheel(0, -12000);
await page.waitForTimeout(800);
assert(Math.abs((await state()).distance - CAMERA.min) < .1);
await page.mouse.wheel(0, 24000);
await page.waitForTimeout(800);
assert(Math.abs((await state()).distance - CAMERA.max) < .1);
checks.push({ test: "Zoom stays in requested 9–25 range" });
assert(await page.evaluate(()=>{const g=window.__game;const p=g.playerPosition.clone();p.y+=.85;p.project(g.camera);return Math.abs(p.x)<1e-6 && Math.abs(p.y)<1e-6;}));
checks.push({ test: "Player remains centered after movement, rotation and zoom" });
await page.keyboard.press("r");
// Do not permit dialogue from across the road.
await page.keyboard.press("e");
assert.equal((await state()).dialogueIndex, -1);
checks.push({ test: "E requires proximity" });
assert(await page.evaluate(() => window.__game.teleport(0.8, -2.6)));
await page.keyboard.press("e");
assert.equal((await state()).dialogueIndex, 0);
checks.push({ test: "E opens nearby Swedish dialogue" });
for (let i = 0; i < 4; i++) await page.keyboard.press("e");
assert.equal((await state()).completed, true);
assert.equal(await page.locator("#money").textContent(), "3 650 kr");
checks.push({ test: "Dialogue completes and awards 250 kr" });
await page.keyboard.press("e");
await page.keyboard.press("e");
assert.equal(await page.locator("#money").textContent(), "3 650 kr");
checks.push({ test: "Reward is granted once" });
assert.equal(
  await page.evaluate(
    () => window.__game.scene.getObjectByName("Cat") !== undefined,
  ),
  false,
);
checks.push({ test: "Cat removed from runtime scene" });
assert.equal(
  await page.evaluate(() => window.__game.teleport(100, 100)),
  false,
);
checks.push({ test: "Boundary rejects street escape" });
assert.deepEqual(errors, []);
checks.push({ test: "No browser runtime errors" });
await page.reload();
await page.waitForFunction(() => window.__game?.ready);
await page.waitForTimeout(1000);
await fs.writeFile(
  ".dream-loop/browser-checks.json",
  JSON.stringify({ checks, errors }, null, 2),
);
console.log(JSON.stringify({ checks, errors }, null, 2));
await browser.close();
