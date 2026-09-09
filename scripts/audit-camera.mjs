import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
const b = await chromium.connectOverCDP(
  (await fs.readFile(".dream-loop/browser-endpoint.txt", "utf8")).trim(),
);
const p = b
  .contexts()[0]
  .pages()
  .find((p) => p.url().includes("5173"));
await p.setViewportSize({ width: 1586, height: 992 });
await p.waitForFunction(() => window.__game?.ready);
await p.evaluate(() => window.__game.setResolution(1586, 992));
const views = [
  ["close", 0, 1.7, -0.72, 0.58, 12],
  ["north", 0, 1.7, Math.PI, 0.65, 36],
  ["west", 0, 1.7, -1.57, 0.6, 36],
  ["east", 0, 1.7, 1.57, 0.65, 36],
  ["edge", 0, -19, Math.PI, 0.52, 36],
];
for (const [name, x, z, yaw, pitch, distance] of views) {
  await p.evaluate(
    ([x, z, yaw, pitch, distance]) => {
      window.__game.teleport(x, z);
      window.__game.setCamera(yaw, pitch, distance);
    },
    [x, z, yaw, pitch, distance],
  );
  await p.waitForTimeout(1800);
  await p.screenshot({ path: ".dream-loop/audit-" + name + ".png" });
  console.log(
    name,
    await p.evaluate(() => {
      const g = window.__game;
      const p = g.playerPosition.clone();
      p.y += 0.85;
      p.project(g.camera);
      let faded = [];
      g.scene.traverse((o) => {
        if (o.name.startsWith("Building") && o.material?.opacity < 0.2)
          faded.push(o.name);
      });
      return { playerNDC: p.toArray(), faded: faded.length, stats: g.stats() };
    }),
  );
}
await p.evaluate(() => {
  window.__game.teleport(0, 1.7);
  window.__game.setCamera(-0.72, 0.53, 28);
});
await b.close();
