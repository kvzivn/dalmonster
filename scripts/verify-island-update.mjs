import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const b=await chromium.connectOverCDP((await fs.readFile('.dream-loop/browser-endpoint.txt','utf8')).trim());
const p=b.contexts()[0].pages().find(p=>p.url().includes('5173'));
await p.reload();
await p.waitForFunction(()=>__game?.ready);
await p.setViewportSize({width:1586,height:992});await p.evaluate(()=>__game.setResolution(1586,992));
const measurements=await p.evaluate(async()=>{
 const T=await import('/node_modules/three/build/three.module.js');
 const size=name=>{const c=__game.scene.getObjectByName(name).clone(true);c.updateMatrixWorld(true);return new T.Box3().setFromObject(c).getSize(new T.Vector3()).toArray();};
 const fence=__game.scene.getObjectByName('IslandPlantingFences');const meshes=[];fence.traverse(o=>{if(o.isMesh)meshes.push(o.name)});
 return {npc:size('NPC'),player:size('Player'),fences:meshes};
});
assert.equal(measurements.fences.length,5);
assert(measurements.npc[1]>measurements.player[1]*1.05);
assert(measurements.npc[0]>measurements.player[0]*1.1);
const facing=[];
for(const [x,z] of [[.8,-2.6],[2.8,-2.8],[1.8,.2]]){
 assert(await p.evaluate(([x,z])=>__game.teleport(x,z),[x,z]));
 await p.keyboard.press('e');await p.waitForTimeout(1100);
 const error=await p.evaluate(()=>{
  const g=__game;const npc=g.scene.getObjectByName('NPC').parent;
  const a=Math.atan2(g.playerPosition.x-g.npcPosition.x,g.playerPosition.z-g.npcPosition.z);
  return {dialogue:g.state.dialogueIndex,error:Math.abs(Math.atan2(Math.sin(a-npc.rotation.y),Math.cos(a-npc.rotation.y)))};
 });
 assert(error.dialogue>=0);assert(error.error<.035,JSON.stringify(error));facing.push({x,z,...error});
 await p.keyboard.press('Escape');
}
await p.evaluate(()=>{__game.teleport(0,1.7);__game.setCamera(-.72,.66,22)});
await p.waitForTimeout(1500);await p.screenshot({path:'.dream-loop/island-fences-gameplay.png'});
await p.evaluate(()=>{__game.teleport(.8,-2.6);__game.setCamera(-2.3,.5,9)});
await p.keyboard.press('e');await p.waitForTimeout(1300);await p.screenshot({path:'.dream-loop/big-black-proportions.png'});
await fs.writeFile('.dream-loop/island-update-checks.json',JSON.stringify({measurements,facing},null,2));console.log({measurements,facing});
await p.keyboard.press('Escape');await b.close();
