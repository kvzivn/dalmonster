import { CAMERA, SPAWN } from "../src/neighbourhood.js";
import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
const browser = await chromium.connectOverCDP(
  (await fs.readFile(".dream-loop/browser-endpoint.txt", "utf8")).trim(),
);
const page = browser
  .contexts()[0]
  .pages()
  .find((p) => p.url().includes("5173"));
await page.setViewportSize({ width: 1920, height: 1080 });
await page.waitForFunction(() => window.__game?.ready);
await page.waitForSelector("#loading", { state: "hidden" });
await page.evaluate(({CAMERA,SPAWN}) => {
  window.__game.setResolution(1920, 1080);
  window.__game.keys.clear();
  window.__game.teleport(SPAWN.x, SPAWN.z);
  window.__game.setCamera(CAMERA.yaw, CAMERA.pitch, CAMERA.distance);
}, {CAMERA,SPAWN});
await page.waitForTimeout(4000);
const metadata = await page.evaluate(() => ({
  userAgent: navigator.userAgent,
  visibility: document.visibilityState,
  hardwareConcurrency: navigator.hardwareConcurrency,
  devicePixelRatio,
  screen: [screen.width, screen.height],
}));
console.log("Idle baseline started");
const idle = await page.evaluate(() => window.__game.benchmark(20));
console.log("Idle", idle);
console.log("Roundabout baseline started");
await page.evaluate(d=>{__game.teleport(0,1.7);__game.setCamera(-.72,.58,d)}, CAMERA.distance);
await page.waitForTimeout(2500);
const island=await page.evaluate(()=>__game.benchmark(15));
console.log("Island",island);
console.log("Moving camera stress test started");
const moving = await page.evaluate(async ({CAMERA,SPAWN}) => {
  const g = window.__game;
  let step = 0;
  const run = setInterval(() => {
    step++;
    g.setCamera(
      -0.72 + step * 0.11,
      0.56 + Math.sin(step * 0.08) * 0.12,
      18 + Math.sin(step * 0.07) * 6,
    );
    g.keys.clear();
    g.keys.add(["KeyW", "KeyD", "KeyS", "KeyA"][Math.floor(step / 18) % 4]);
  }, 200);
  const result = await g.benchmark(30);
  clearInterval(run);
  g.keys.clear();
  g.setCamera(CAMERA.yaw, CAMERA.pitch, CAMERA.distance);
  g.teleport(SPAWN.x,SPAWN.z);
  return result;
}, {CAMERA,SPAWN});
console.log("Moving", moving);
const report = { date: new Date().toISOString(), metadata, idle, island, moving };
await fs.writeFile(
  process.argv[2] || ".dream-loop/performance.json",
  JSON.stringify(report, null, 2),
);
await browser.close();
