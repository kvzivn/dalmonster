import {chromium} from '@playwright/test';import fs from 'node:fs/promises';import assert from 'node:assert/strict';import {CAMERA} from '../src/neighbourhood.js';
const b=await chromium.connectOverCDP((await fs.readFile('.dream-loop/browser-endpoint.txt','utf8')).trim());const p=b.contexts()[0].pages().find(p=>p.url().includes('5173'));const errors=[];p.on('pageerror',e=>errors.push(String(e)));
await p.reload();await p.waitForFunction(()=>__game?.ready);await p.waitForSelector("#loading",{state:"hidden"});await p.waitForTimeout(500);await p.setViewportSize({width:1586,height:992});await p.evaluate(()=>__game.setResolution(1586,992));
const initial=await p.evaluate(()=>__game.state);assert(Math.abs(initial.distance-CAMERA.distance)<.01);
await p.mouse.move(1100,750);await p.mouse.down();await p.mouse.move(1100,100,{steps:10});await p.mouse.up();await p.waitForTimeout(900);assert(Math.abs((await p.evaluate(()=>__game.state.pitch))-CAMERA.minPitch)<.01);
await p.keyboard.press('r');await p.waitForTimeout(900);await p.screenshot({path:'.dream-loop/refined-arrival-final.png'});
assert(await p.evaluate(()=>!!__game.scene.getObjectByName('Arrival_Unique_Granite_Setts')));
await p.evaluate(()=>{__game.teleport(0,17);__game.setCamera(-.72,.56,9)});await p.waitForTimeout(700);await p.keyboard.down('w');
const sample=await p.evaluate(async()=>{
 const T=await import('/node_modules/three/build/three.module.js');const model=__game.scene.getObjectByName('Player'),root=model.parent;const samples=[];
 for(let i=0;i<90;i++){await new Promise(r=>setTimeout(r,33));const m=root.userData.motion;if(!m)continue;const foot=model.getObjectByName('LeftFoot'),knee=model.getObjectByName('LeftKnee');const pos=foot.getWorldPosition(new T.Vector3());
 samples.push({blend:m.blend,contact:m.leftContact,ankleY:pos.y-__game.playerPosition.y,knee:knee.quaternion.x,p:pos.toArray(),phase:m.phase});}
 return samples;
});await p.screenshot({path:'.dream-loop/refined-walk-final.png'});await p.keyboard.up('w');await p.waitForTimeout(900);
const planted=sample.filter(s=>s.contact&&s.blend>.99);assert(planted.length>10);assert(planted.every(s=>Math.abs(s.ankleY-.13)<.035),JSON.stringify(planted.slice(0,4)));assert(sample.some(s=>Math.abs(s.knee)>.2));
await p.evaluate(()=>{__game.teleport(.8,-2.6);__game.setCamera(2.6,.53,9)});await p.keyboard.press('e');await p.waitForTimeout(1300);await p.screenshot({path:'.dream-loop/refined-npc-final.png'});assert((await p.evaluate(()=>__game.state.dialogueIndex))>=0);await p.keyboard.press('Escape');
const characterRigs=await p.evaluate(()=>['Player','NPC','StreetPedestrian_A','StreetPedestrian_B'].map(name=>{const root=__game.scene.getObjectByName(name);let count=0;root.traverse(o=>{if(o.isSkinnedMesh)count++});return{name,skins:count,knee:!!root.getObjectByName('LeftKnee'),elbow:!!root.getObjectByName('RightElbow')}}));assert(characterRigs.every(x=>x.skins&&x.knee&&x.elbow));assert.deepEqual(errors,[]);
const report={initial,lowerPitch:CAMERA.minPitch,characterRigs,plantedAnkleHeight:{min:Math.min(...planted.map(s=>s.ankleY)),max:Math.max(...planted.map(s=>s.ankleY))},samples:sample,errors};await fs.writeFile('.dream-loop/refinement-browser-checks.json',JSON.stringify(report,null,2));console.log({...report,samples:sample.length});await b.close();
