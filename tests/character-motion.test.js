import {test} from 'node:test';
import assert from 'node:assert/strict';
import {footStep,solveLeg} from '../src/character-motion.js';
test('planted foot stays on the floor and cancels forward body displacement',()=>{
 const stride=1.02;
 for(let u=.02;u<.58;u+=.02){const a=footStep(u*Math.PI*2,stride),b=footStep((u+.01)*Math.PI*2,stride);assert(a.contact);assert.equal(a.lift,0);assert(Math.abs((b.z-a.z)+stride*.01)<1e-9);}
});
test('swing clears the ground and returns continuously to the next contact',()=>{
 assert(footStep(.8*Math.PI*2).lift>.08);assert(!footStep(.8*Math.PI*2).contact);
 const a=footStep(2*Math.PI-1e-5),b=footStep(0);assert(Math.abs(a.z-b.z)<1e-5);assert(a.lift<1e-5);
});
test('knee and ankle solution reaches foot targets with a level sole',()=>{
 for(const forward of [-.24,0,.24])for(const height of [.52,.63]){
  const {hip,knee,ankle}=solveLeg(.405,.315,height,forward);
  const y=.405*Math.cos(hip)+.315*Math.cos(hip+knee),z=-.405*Math.sin(hip)-.315*Math.sin(hip+knee);
  assert(Math.abs(y-height)<1e-8);assert(Math.abs(z-forward)<1e-8);assert(knee>0);assert(Math.abs(hip+knee+ankle)<1e-8);
 }
});
test('unreachable targets are clamped without NaN or inverted knees',()=>{
 for(const h of [0,.1,1.4])for(const z of [-2,0,2]){const p=solveLeg(.405,.315,h,z);assert(Object.values(p).every(Number.isFinite));assert(p.knee>=0);}
});
