import * as THREE from 'three';

// One original Blender mesh with individually fitted courses and unique face UVs.
// The existing ground bake/reflection pass keeps this detail inexpensive.
export function buildArrivalStreet(scene, asset, granite, world) {
  const material = new THREE.MeshStandardMaterial({
    name:'Arrival hand laid wet granite', map:granite, bumpMap:granite,
    bumpScale:.0018, color:0xc0bcb1, roughness:.7, vertexColors:true,
  });
  material.userData.wetStrength=.58;
  world.addGroundShader(material);
  const baseCompile=material.onBeforeCompile;
  material.onBeforeCompile=shader=>{
    baseCompile(shader);
    shader.fragmentShader=shader.fragmentShader.replace(
      'roughnessFactor=mix(.14,.55,smoothstep(-.3,.7,wetPatch));',
      `float across=worldGround.x*.608761-worldGround.z*.793353;
       float wheelWear=exp(-pow((abs(across)-1.13)*2.8,2.));
       roughnessFactor=mix(.23,.69,smoothstep(-.3,.7,wetPatch));
       roughnessFactor=mix(roughnessFactor,.25,wheelWear*.32);`
    );
  };
  material.customProgramCacheKey=()=> 'arrival-unique-setts-v1';
  asset.traverse(o=>{
    if (!o.isMesh) return;
    o.material=material;o.receiveShadow=true;world.reflectionSurfaces.push(o);
  });
  scene.add(asset);
}
