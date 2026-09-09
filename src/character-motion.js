import * as THREE from 'three';

const TAU=Math.PI*2;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
// Contact, recoil, passing and lift: the planted foot moves backward at a
// constant rate while the body advances; only the recovery foot lifts.
export function footStep(phase, strideLength=1.02, running=false) {
  const u=((phase/TAU)%1+1)%1, stance=running?.43:.60, half=strideLength*stance/2;
  if(u<stance)return {z:half-u/stance*half*2,lift:0,contact:true};
  const v=(u-stance)/(1-stance), ease=v*v*(3-2*v);
  return {z:-half+ease*half*2,lift:(running?.16:.105)*Math.sin(Math.PI*v)**1.4,contact:false};
}
// Two-link sagittal IK with the knee bending forward and the shin backward.
export function solveLeg(upper,lower,height,forward) {
  const distance=Math.min(upper+lower-.0001,Math.max(Math.abs(upper-lower)+.0001,Math.hypot(height,forward)));
  const direction=-Math.atan2(forward,height);
  const hip=direction-Math.acos(clamp((upper*upper+distance*distance-lower*lower)/(2*upper*distance),-1,1));
  const knee=Math.acos(clamp((distance*distance-upper*upper-lower*lower)/(2*upper*lower),-1,1));
  return {hip,knee,ankle:-hip-knee};
}
const caches=new WeakMap(),axisX=new THREE.Vector3(1,0,0),q=new THREE.Quaternion();
function cache(root){
  let a=caches.get(root);if(a)return a;
  a={blend:0,nodes:{},rest:{},body:null};
  for(const name of ['LeftLeg','RightLeg','LeftKnee','RightKnee','LeftFoot','RightFoot','LeftArm','RightArm','LeftElbow','RightElbow','Head','Backpack']){
    const node=root.getObjectByName(name);if(node){a.nodes[name]=node;a.rest[name]=node.quaternion.clone();}
  }
  const model=a.nodes.LeftLeg?.parent;
  if(model){
    root.updateMatrixWorld(true);
    const body=new THREE.Group();body.name='CharacterUpperBodyMotion';body.position.y=a.nodes.LeftLeg.position.y;model.add(body);body.updateMatrixWorld(true);
    for(const child of [...model.children]){
      if(child===body)continue;
      if(['Head','Backpack','LeftArm','RightArm'].includes(child.name)||child.isMesh)body.attach(child);
    }
    a.body=body;a.bodyBase=body.position.clone();
  }
  a.hipHeight=a.nodes.LeftLeg?.position.y??.85;
  a.upper=Math.abs(a.nodes.LeftKnee?.position.y??.405);
  a.lower=Math.abs(a.nodes.LeftFoot?.position.y??(a.hipHeight-.535));
  caches.set(root,a);return a;
}
function turn(a,name,x=0,y=0,z=0){
 const node=a.nodes[name];if(!node)return;
 node.quaternion.copy(a.rest[name]);q.setFromAxisAngle(axisX,x);node.quaternion.multiply(q);
 if(y||z){node.rotateY(y);node.rotateZ(z);}
}
export function animateCharacter(root,time,moving,phase,baseY,amplitude=.43,dt=1/30){
 if(!root)return;
 const a=cache(root),blendTarget=moving?1:0;
 a.blend+=(blendTarget-a.blend)*(1-Math.exp(-dt*(moving?8:12)));
 if(a.blend<.0001)a.blend=0;
 const blend=a.blend,running=!!root.userData.running,strideLength=root.userData.strideLength??1.02;
 const dip=(-.019-.051*Math.abs(Math.cos(phase)))*blend;
 root.position.y=baseY+dip;
 for(const [side,offset] of [['Left',0],['Right',Math.PI]]){
   const step=footStep(phase+offset,strideLength,running);
   const pose=solveLeg(a.upper,a.lower,a.hipHeight+dip-.13-step.lift,step.z);
   turn(a,side+'Leg',pose.hip*blend);
   turn(a,side+'Knee',pose.knee*blend);
   turn(a,side+'Foot',pose.ankle*blend);
   const carry=root.name==='StreetPedestrian_A'&&side==='Left'?.42:1;
   const swing=Math.cos(phase+offset)*amplitude*.58*blend*carry;
   turn(a,side+'Arm',swing-.035,0,(side==='Left'?1:-1)*.014);
   const gesture=root.userData.talking&&side==='Right'?-.09*(.5+.5*Math.sin(time*2.1)):0;
   turn(a,side+'Elbow',-.09-blend*(.10+.07*Math.max(0,-Math.cos(phase+offset)))+gesture);
 }
 if(a.body){
   a.body.position.x=a.bodyBase.x+Math.sin(phase)*.014*blend;
   a.body.rotation.set(-.018*blend,Math.sin(phase)*.036*blend,Math.sin(phase+.3)*.012*blend);
   const breath=Math.sin(time*1.65)*.0018;
   a.body.scale.set(1+breath,1+breath*.65,1+breath*1.5);
 }
 turn(a,'Head',Math.sin(time*.93)*.012+(root.userData.talking?Math.sin(time*2.2)*.018:0),Math.sin(time*.55)*.038);
 turn(a,'Backpack',Math.sin(phase-.35)*.018*blend+Math.sin(time*1.65)*.003,0,Math.sin(phase+.5)*.009*blend);
 root.userData.motion={blend,dip,phase,strideLength,running,leftContact:footStep(phase,strideLength,running).contact};
}
