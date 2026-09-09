import { isInsidePlayableArea, streetPoint, SPAWN } from "../src/neighbourhood.js";
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  canOccupy,
  moveWithCollision,
  cameraRelativeInput,
  insideEllipse,
} from "../src/collision.js";
test("camera-relative movement remains normalized at any heading", () => {
  for (const yaw of [0, Math.PI / 2, Math.PI, -0.8]) {
    const forward = cameraRelativeInput(new Set(["KeyW"]), yaw),
      arrow = cameraRelativeInput(new Set(["ArrowUp"]), yaw),
      diagonal = cameraRelativeInput(new Set(["KeyW", "KeyD"]), yaw);
    assert.deepEqual(forward, arrow);
    assert.ok(Math.abs(Math.hypot(diagonal.x, diagonal.z) - 1) < 1e-10);
    assert.ok(Math.abs(forward.x + Math.sin(yaw)) < 1e-10);
    assert.ok(Math.abs(forward.z + Math.cos(yaw)) < 1e-10);
  }
});
test("opposing keys cancel", () =>
  assert.equal(
    cameraRelativeInput(new Set(["KeyW", "KeyS", "KeyA", "KeyD"]), 0.5).moving,
    false,
  ));
test("large movement cannot tunnel through a column", () => {
  const p = { x: 0, z: 0 };
  moveWithCollision(p, 10, 0, [{ type: "circle", x: 3, z: 0, r: 0.5 }]);
  assert.ok(p.x < 2.23);
  assert.equal(p.z, 0);
});
test("diagonal movement slides along collision instead of sticking", () => {
  const p = { x: 0, z: 0 };
  moveWithCollision(p, 4, 2, [{ type: "box", x: 2, z: 0, w: 1, d: 3 }]);
  assert.ok(p.z > 1.8);
  assert.ok(canOccupy(p.x, p.z, [{ type: "box", x: 2, z: 0, w: 1, d: 3 }]));
});
test("island beds enforce their rotated footprint", () => {
  const b = { type: "ellipse", x: 3, z: 4, rx: 1, rz: 3, angle: Math.PI / 2 };
  assert.equal(insideEllipse(5, 4, b), true);
  assert.equal(insideEllipse(3, 6, b), false);
  assert.equal(canOccupy(5, 4, [b]), false);
});
test("outer boundary contains player on every approach", () => {
  for (let i = 0; i < 32; i++) {
    const a = (i / 32) * Math.PI * 2,
      p = { x: 0, z: 0 };
    moveWithCollision(p, Math.cos(a) * 100, Math.sin(a) * 100, []);
    assert.ok(isInsidePlayableArea(p.x,p.z));
  }
});

test("new central layout leaves a broad unobstructed north-south corridor", async () => {
  const {readFile}=await import('node:fs/promises');
  const layout=JSON.parse(await readFile(new URL('../src/layout.json',import.meta.url),'utf8'));
  const obstacles=layout.beds.map(b=>({type:'ellipse',...b}));
  for(let z=-4;z<=4;z+=.2) for(const x of [-.5,0,.5]) assert(canOccupy(x,z,obstacles),`path blocked at ${x},${z}`);
});
test("curved border planting blocks soil while keeping inner paths and outer road open", async()=>{
  const {readFile}=await import('node:fs/promises');
  const layout=JSON.parse(await readFile(new URL('../src/layout.json',import.meta.url),'utf8'));
  const obstacles=layout.borderBeds.map(b=>({type:'border',...b}));
  for(const b of layout.borderBeds) {
    const a=(b.start+b.end)/2;
    assert.equal(canOccupy(Math.sin(a)*9.4,Math.cos(a)*12.2,obstacles),false);
    assert.equal(canOccupy(Math.sin(a)*7.5,Math.cos(a)*10,obstacles),true);
    assert.equal(canOccupy(Math.sin(a)*12,Math.cos(a)*15,obstacles),true);
  }
  assert(canOccupy(0,12,obstacles));assert(canOccupy(0,-12,obstacles));
});

test("arrival street is connected and bounded, while building footprints stay solid", async () => {
  const { readFile } = await import('node:fs/promises');
  const all = JSON.parse(await readFile(new URL('../public/assets/environment-collisions.json',import.meta.url)));
  assert(canOccupy(SPAWN.x,SPAWN.z,all));
  for(let t=12;t<41;t+=.2) { const p=streetPoint(t);assert(canOccupy(p.x,p.z,all),`arrival blocked at ${t}`); }
  for(const t of [43,50,65]) { const p=streetPoint(t);assert(!canOccupy(p.x,p.z,all)); }
  assert(!canOccupy(-22,-24,all), 'north building is solid');
  assert(!canOccupy(-30,-12,all), 'west building is solid');
});
test("street pedestrian routes remain outside island and avoid fixed obstructions", async () => {
  const { pedestrianRoutes } = await import('../src/pedestrians.js');
  const { readFile } = await import('node:fs/promises');
  const all = JSON.parse(await readFile(new URL('../public/assets/environment-collisions.json',import.meta.url)));
  for(const route of pedestrianRoutes) for(let i=1;i<route.length;i++) for(let f=0;f<=1;f+=.02) {
    const x=route[i-1].x*(1-f)+route[i].x*f,z=route[i-1].z*(1-f)+route[i].z*f;
    assert((x/11)**2+(z/14)**2>1.1);assert(canOccupy(x,z,all,.25),`walker blocked ${x},${z}`);
  }
});
