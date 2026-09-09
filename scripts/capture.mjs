import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
const browser = await chromium.connectOverCDP(
  (await fs.readFile(".dream-loop/browser-endpoint.txt", "utf8")).trim(),
);
const page = browser
  .contexts()[0]
  .pages()
  .find((p) => p.url().includes("5173"));
const width = Number(process.argv[3] || 1920),
  height = Number(process.argv[4] || 1080);
await page.setViewportSize({ width, height });
await page.waitForFunction(() => window.__game?.ready);
await page.waitForSelector("#loading", { state: "hidden" });
await page.evaluate(
  ([w, h]) => window.__game.setResolution(w, h),
  [width, height],
);
await page.waitForTimeout(900);
await page.screenshot({ path: process.argv[2] || ".dream-loop/current.png" });
console.log(await page.evaluate(() => window.__game.stats()));
await browser.close();
