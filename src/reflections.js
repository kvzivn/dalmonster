import * as THREE from "three";
import { Reflector } from "three/addons/objects/Reflector.js";
// One low-resolution planar capture. No screen-space ray marching or temporal history.
export function createWetReflection() {
  const mirror = new Reflector(new THREE.PlaneGeometry(1, 1), {
    textureWidth: 768,
    textureHeight: 432,
    multisample: 0,
    clipBias: 0.003,
  });
  mirror.rotation.x = -Math.PI / 2;
  mirror.position.y = 0.01;
  mirror.updateMatrixWorld();
  const matrix = new THREE.Matrix4();
  const inverse = mirror.matrixWorld.clone().invert();
  return {
    texture: mirror.getRenderTarget().texture,
    matrix,
    render(renderer, scene, camera, surfaces) {
      const previous = surfaces.map((m) => m.visible);
      surfaces.forEach((m) => (m.visible = false));
      camera.updateMatrixWorld();
      mirror.onBeforeRender(renderer, scene, camera);
      surfaces.forEach((m, i) => (m.visible = previous[i]));
      matrix
        .copy(mirror.material.uniforms.textureMatrix.value)
        .multiply(inverse);
    },
    dispose() {
      mirror.dispose();
      mirror.geometry.dispose();
    },
  };
}
