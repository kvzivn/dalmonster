import * as THREE from "three";

// Original Blender fan-laid stones. Per-instance polar coordinates bend the
// complete tile exactly into the oval road, without straight-edged wedge gaps.
export function buildStoneRoad(scene, asset, granite, world) {
  const rows = 4, columns = 44, tileSize = 2.4;
  const roadGrain = granite.clone();
  roadGrain.repeat.set(0.2,0.2);
  const placements = [[], [], []];
  const roadBatches = [];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < columns; col++) {
      const variant = (col * 7 + row * 11 + Math.floor(col / 5)) % 3;
      placements[variant].push({
        angle: (col + 0.5) * Math.PI * 2 / columns,
        radial: (row + 0.5) / rows,
        tone: 0.90 + 0.09 * Math.sin(col * 9.7 + row * 5.1),
      });
    }
  }
  for (let variant = 0; variant < 3; variant++) {
    const source = asset.getObjectByName(`RoadFan_${variant}`);
    if (!source?.geometry) throw new Error(`Missing Blender RoadFan_${variant}`);
    const geometry = source.geometry.clone();
    const instances = placements[variant];
    const polar = new Float32Array(instances.length * 4);
    instances.forEach((p, i) => polar.set([
      p.angle, p.radial, Math.PI * 2 / columns / tileSize, 1 / rows / tileSize,
    ], i * 4));
    geometry.setAttribute("aPolar", new THREE.InstancedBufferAttribute(polar, 4));
    const material = new THREE.MeshStandardMaterial({
      name: "Wet hand-laid road granite", map: roadGrain, bumpMap: roadGrain,
      bumpScale: 0.0035, color: 0xa0a7ab, roughness: 0.62,
      vertexColors: !!geometry.attributes.color,
    });
    material.userData.wetStrength = 0.90;
    world.addGroundShader(material);
    const bakeShader = material.onBeforeCompile;
    material.onBeforeCompile = (shader) => {
      bakeShader(shader);
      shader.vertexShader = shader.vertexShader
        .replace("#include <common>", "#include <common>\nattribute vec4 aPolar;")
        .replace("#include <beginnormal_vertex>", `#include <beginnormal_vertex>
          float roadAngle = aPolar.x + position.x * aPolar.z;
          float roadT = aPolar.y + position.z * aPolar.w;
          vec2 roadTangent = normalize(vec2((11.+9.2*roadT)*cos(roadAngle), -(14.+8.22*roadT)*sin(roadAngle)));
          vec2 roadNormal = normalize(vec2(9.2*sin(roadAngle),8.22*cos(roadAngle)));
          objectNormal = vec3(objectNormal.x*roadTangent.x+objectNormal.z*roadNormal.x, objectNormal.y, objectNormal.x*roadTangent.y+objectNormal.z*roadNormal.y);
        `)
        .replace("#include <begin_vertex>", `#include <begin_vertex>
          transformed=vec3(sin(roadAngle)*(11.+9.2*roadT),position.y*.65,cos(roadAngle)*(14.+8.22*roadT));
        `);
    };
    material.customProgramCacheKey = () => "polar-granite-road-v1";
    const mesh = new THREE.InstancedMesh(geometry, material, instances.length);
    mesh.name = `Individually cut road fans ${variant}`;
    const identity = new THREE.Matrix4();
    instances.forEach((p,i) => {
      mesh.setMatrixAt(i, identity);
      mesh.setColorAt(i, new THREE.Color().setScalar(p.tone));
    });
    mesh.frustumCulled = false;
    mesh.receiveShadow = true;
    mesh.renderOrder = 1;
    scene.add(mesh);
    world.reflectionSurfaces.push(mesh);
    roadBatches.push({ mesh, instances, polar });
  }
  // Keep only subdued, rough grout beneath the modeled stones.
  world.roadBase.material.map = granite;
  world.roadBase.material.bumpMap = granite;
  world.roadBase.material.bumpScale = 0.001;
  world.roadBase.material.color.setHex(0x656966);
  world.roadBase.material.userData.wetStrength = 0.04;
  world.roadBase.position.y = 0.003;
  const frustum = new THREE.Frustum(), projection = new THREE.Matrix4();
  const bounds = new THREE.Sphere(new THREE.Vector3(), 2.3);
  return {
    update(camera) {
      camera.updateMatrixWorld();
      frustum.setFromProjectionMatrix(projection.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse));
      for (const {mesh, instances, polar} of roadBatches) {
        let count = 0;
        for (const p of instances) {
          bounds.center.set(Math.sin(p.angle)*(11+9.2*p.radial),0.01,Math.cos(p.angle)*(14+8.22*p.radial));
          if (!frustum.intersectsSphere(bounds)) continue;
          polar.set([p.angle,p.radial,Math.PI*2/columns/tileSize,1/rows/tileSize],count*4);
          mesh.instanceColor.array.set([p.tone,p.tone,p.tone],count*3);
          count++;
        }
        mesh.count = count;
        mesh.geometry.attributes.aPolar.needsUpdate = true;
        mesh.instanceColor.needsUpdate = true;
      }
    },
  };
}
