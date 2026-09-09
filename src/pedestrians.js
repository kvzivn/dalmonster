import { canOccupy } from './collision.js';
import { streetPoint, groundHeight } from './neighbourhood.js';

// Both routes stay on road surfaces outside the island. They never receive an interaction target.
export const pedestrianRoutes = [
  [streetPoint(26, 1.8), streetPoint(37, 1.8)],
  [{x:-12.5,z:-12}, {x:-9,z:-16.2}, {x:-3,z:-18.2}, {x:4,z:-18}],
];
export function createPedestrians(roots, scene, obstacles) {
  const states = roots.map((root, index) => {
    const route = pedestrianRoutes[index];
    root.name = `StreetPedestrian_${index === 0 ? 'A' : 'B'}`;
    root.userData.interactive = false;
    const p = route[index ? 2 : 0];
    root.position.set(p.x, groundHeight(p.x,p.z), p.z);
    scene.add(root);
    const collider={type:"circle",x:p.x,z:p.z,r:.27,name:root.name};
    obstacles.push(collider);
    return { root, collider, route, index: index ? 3 : 1, direction: 1, speed: index ? .91 : .76, phase: index * 2, wait: index ? 0 : 1.3, moving: false };
  });
  return { roots, states, update(dt, time, player, animate) {
    for (const s of states) {
      const p = s.root.position, target = s.route[s.index];
      const dx = target.x-p.x, dz = target.z-p.z, length = Math.hypot(dx,dz);
      s.moving = false;
      if (s.wait > 0) s.wait -= dt;
      else if (length < .12) {
        if (s.index === 0 || s.index === s.route.length-1) { s.direction *= -1; s.wait = 1.8 + s.speed; }
        s.index += s.direction;
      } else {
        const step = Math.min(length, s.speed * dt);
        const x = p.x + dx/length*step, z = p.z + dz/length*step;
        const playerAhead = Math.hypot(x-player.x,z-player.z) < .85;
        if (!playerAhead && canOccupy(x,z,obstacles,.25,s.collider)) {
          p.x=x; p.z=z; s.collider.x=x; s.collider.z=z; s.moving=true; s.phase += step*Math.PI*2/1.02;
        }
        const yaw = Math.atan2(dx,dz);
        s.root.rotation.y += Math.atan2(Math.sin(yaw-s.root.rotation.y),Math.cos(yaw-s.root.rotation.y))*(1-Math.exp(-dt*5));
      }
      animate(s.root,time+s.speed*4,s.moving,s.phase,groundHeight(p.x,p.z),.32);
    }
  }};
}
