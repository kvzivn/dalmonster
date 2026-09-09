import * as THREE from "three";

// Small quarter-resolution lens glow. Only bright highlights enter the blur.
// The scene stays HDR until one final tone-map; no AO, depth effects or temporal history.
export function createNightBloom(renderer) {
  const hdr = new THREE.WebGLRenderTarget(1, 1, {
    type: THREE.HalfFloatType,
    samples: 2,
  });
  const glowA = new THREE.WebGLRenderTarget(1, 1, {
    type: THREE.HalfFloatType,
    depthBuffer: false,
  });
  const glowB = glowA.clone();
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const vertexShader = `varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}`;
  const threshold = new THREE.ShaderMaterial({
    toneMapped: false,
    depthTest: false,
    depthWrite: false,
    vertexShader,
    uniforms: { source: { value: hdr.texture } },
    fragmentShader: `uniform sampler2D source;varying vec2 vUv;void main(){vec3 c=texture2D(source,vUv).rgb;float b=max(c.r,max(c.g,c.b));float weight=smoothstep(.85,1.7,b);gl_FragColor=vec4(c*weight,1.);}`,
  });
  const blur = new THREE.ShaderMaterial({
    toneMapped: false,
    depthTest: false,
    depthWrite: false,
    vertexShader,
    uniforms: {
      source: { value: glowA.texture },
      axis: { value: new THREE.Vector2() },
    },
    fragmentShader: `uniform sampler2D source;uniform vec2 axis;varying vec2 vUv;void main(){vec3 c=texture2D(source,vUv).rgb*.227027;c+=texture2D(source,vUv+axis*1.384615).rgb*.316216;c+=texture2D(source,vUv-axis*1.384615).rgb*.316216;c+=texture2D(source,vUv+axis*3.230769).rgb*.07027;c+=texture2D(source,vUv-axis*3.230769).rgb*.07027;gl_FragColor=vec4(c,1.);}`,
  });
  const composite = new THREE.ShaderMaterial({
    depthTest: false,
    depthWrite: false,
    vertexShader,
    uniforms: {
      source: { value: hdr.texture },
      glow: { value: glowA.texture },
      strength: { value: 0.19 },
    },
    fragmentShader: `uniform sampler2D source;uniform sampler2D glow;uniform float strength;varying vec2 vUv;void main(){gl_FragColor=vec4(texture2D(source,vUv).rgb+texture2D(glow,vUv).rgb*strength,1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), threshold);
  quad.frustumCulled = false;
  scene.add(quad);
  const size = new THREE.Vector2();
  return {
    enabled: true,
    render(world, view) {
      renderer.getDrawingBufferSize(size);
      if (hdr.width !== size.x || hdr.height !== size.y) {
        hdr.setSize(size.x, size.y);
        glowA.setSize(
          Math.max(1, Math.round(size.x / 4)),
          Math.max(1, Math.round(size.y / 4)),
        );
        glowB.setSize(glowA.width, glowA.height);
      }
      renderer.setRenderTarget(hdr);
      renderer.render(world, view);
      quad.material = threshold;
      renderer.setRenderTarget(glowA);
      renderer.render(scene, camera);
      quad.material = blur;
      blur.uniforms.source.value = glowA.texture;
      blur.uniforms.axis.value.set(1 / glowA.width, 0);
      renderer.setRenderTarget(glowB);
      renderer.render(scene, camera);
      blur.uniforms.source.value = glowB.texture;
      blur.uniforms.axis.value.set(0, 1 / glowA.height);
      renderer.setRenderTarget(glowA);
      renderer.render(scene, camera);
      quad.material = composite;
      renderer.setRenderTarget(null);
      renderer.render(scene, camera);
    },
  };
}
