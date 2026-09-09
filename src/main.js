import "./style.css";
import { CAMERA, SPAWN, groundHeight } from "./neighbourhood.js";
import { buildArrivalStreet } from "./arrival-street.js";
import { animateCharacter } from "./character-motion.js";
import { createPedestrians } from "./pedestrians.js";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import {
  buildWorld,
  makeEnvironment,
  makeLamp,
  lamps,
  parkedCars,
  obstacles,
} from "./world.js";
import { createNightBloom } from "./bloom.js";
import { buildStoneRoad } from "./road.js";
import { createWetReflection } from "./reflections.js";
import {
  moveWithCollision,
  cameraRelativeInput,
  canOccupy,
} from "./collision.js";
const $ = (id) => document.getElementById(id);
const canvas = $("world");
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: "high-performance",
  alpha: false,
});
const gl = renderer.getContext();
const gpuInfo = gl.getExtension("WEBGL_debug_renderer_info");
const gpuName = gpuInfo ? gl.getParameter(gpuInfo.UNMASKED_RENDERER_WEBGL) : "";
const isBaseM1 = /Apple M1[,)]/.test(gpuName);
let frameLimit = isBaseM1 ? 30 : 60;
function screenPixelRatio() {
  const maxPixels = isBaseM1 ? 1920 * 1080 : 3200 * 1800;
  return Math.min(
    devicePixelRatio,
    1.5,
    Math.sqrt(maxPixels / (innerWidth * innerHeight)),
  );
}
renderer.setPixelRatio(screenPixelRatio());
renderer.setSize(innerWidth, innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;
renderer.info.autoReset = false;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x181e25);
scene.fog = new THREE.FogExp2(0x242a32, 0.014);
scene.environment = makeEnvironment(renderer);
scene.environmentIntensity = 0.65;
const camera = new THREE.PerspectiveCamera(
  42,
  innerWidth / innerHeight,
  0.2,
  170,
);
const clock = new THREE.Clock();
const keys = new Set();
const playerPosition = new THREE.Vector3(SPAWN.x, .012, SPAWN.z),
  npcPosition = new THREE.Vector3(1.8, 0.15, -1.5);
let yaw = CAMERA.yaw,
  pitch = CAMERA.pitch,
  distance = CAMERA.distance,
  targetDistance = CAMERA.distance,
  targetYaw = yaw,
  targetPitch = pitch;
const occluders = [];
const buildingOccluders = new Map();
const cameraRay = new THREE.Raycaster();
let occlusionTime = 0;
let player,
  npc,
  pedestrians,
  world,
  ready = false,
  dialogueIndex = -1,
  completed = false,
  toastTimer,
  boundaryTimer,
  walkPhase = 0;
const hemi = new THREE.HemisphereLight(0x9aaec0, 0x566078, 1.1);
scene.add(hemi);
const key = new THREE.DirectionalLight(0xffd49a, .95);
key.position.set(-9, 18, -7);
key.castShadow = true;
Object.assign(key.shadow.camera, {
  left: -28,
  right: 28,
  top: 30,
  bottom: -28,
  near: 1,
  far: 70,
});
key.shadow.mapSize.set(2048, 2048);
key.shadow.normalBias = 0.055;
key.shadow.bias = -0.00015;
key.shadow.radius = 2;
scene.add(key);
key.target.position.set(0, 0, 0);
scene.add(key.target);
key.shadow.autoUpdate = false;
key.shadow.needsUpdate = true;
const characterLight = new THREE.DirectionalLight(0xfbd4a0, 0.65);
characterLight.castShadow = true;
characterLight.shadow.mapSize.set(512, 512);
Object.assign(characterLight.shadow.camera, {
  left: -4,
  right: 4,
  top: 4,
  bottom: -4,
  near: 1,
  far: 22,
});
characterLight.shadow.normalBias = 0.035;
characterLight.shadow.bias = -0.0002;
characterLight.shadow.radius = 3;
characterLight.position.set(-4, 8, -3);
scene.add(characterLight, characterLight.target);
const moon = new THREE.DirectionalLight(0x86a7ba, 0.32);
moon.position.set(20, 30, 8);
scene.add(moon);
for (const [x, z, h] of [lamps[0], lamps[2], lamps[4]]) {
  const l = new THREE.PointLight(0xffbd70, 18, 12, 2);
  l.position.set(x, h - 0.25, z);
  scene.add(l);
}
const localFill = new THREE.PointLight(0xffd4a7, 32, 9, 2);
localFill.position.set(1.5, 3.6, 0.3);
scene.add(localFill);
const shopFill = new THREE.PointLight(0xffc080, 28, 9, 2);
shopFill.position.set(-21.624, 2.463, -21.240);
scene.add(shopFill);
const wetReflection = createWetReflection();
const nightBloom = createNightBloom(renderer);
const loader = new GLTFLoader(),
  tl = new THREE.TextureLoader();
async function init() {
  try {
    const [
      cobble,
      asphalt,
      granite,
      pavers,
      soil,
      groundDetails,
      env,
      p,
      n,
      collisionData,
    ] = await Promise.all([
      tl.loadAsync("/assets/cobblestone-fan.png"),
      tl.loadAsync("/assets/asphalt.png"),
      tl.loadAsync("/assets/granite-grain.png"),
      loader.loadAsync("/assets/pavers.glb"),
      tl.loadAsync("/assets/soil-autumn.png"),
      loader.loadAsync("/assets/leaf.glb"),
      loader.loadAsync("/assets/environment-web.glb"),
      loader.loadAsync("/assets/player-refined.glb"),
      loader.loadAsync("/assets/npc-refined.glb"),
      fetch("/assets/environment-collisions.json").then((r) => r.json()),
    ]);
    const groundLight = await tl.loadAsync("/assets/ground-lightmap.png");
    groundLight.colorSpace = THREE.SRGBColorSpace;
    world = buildWorld(scene, {
      cobble,
      asphalt,
      granite,
      pavers: pavers.scene,
      soil,
      groundDetails: groundDetails.scene,
      lightMap: groundLight,
      wetReflection,
    });
    const roadFans = await loader.loadAsync("/assets/road-fan.glb");
    world.stoneRoad = buildStoneRoad(scene, roadFans.scene, granite, world);
    const arrivalSetts = await loader.loadAsync("/assets/arrival-setts.glb");
    buildArrivalStreet(scene, arrivalSetts.scene, granite, world);
    const fences = await loader.loadAsync("/assets/island-fences.glb");
    fences.scene.name = "IslandPlantingFences";
    fences.scene.traverse(o => {
      if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
    });
    scene.add(fences.scene);
    const plants = await loader.loadAsync("/assets/planting.glb");
    const borderPlants = await loader.loadAsync("/assets/border-planting.glb");
    plants.scene.add(borderPlants.scene);
    scene.add(plants.scene);
    world.plantMaterials = [];
    plants.scene.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        if (!o.name.includes("Stones")) {
          o.material.onBeforeCompile = (shader) => {
            shader.uniforms.uTime = { value: 0 };
            o.material.userData.shader = shader;
            shader.vertexShader = shader.vertexShader
              .replace(
                "#include <common>",
                "#include <common>\nuniform float uTime;",
              )
              .replace(
                "#include <begin_vertex>",
                "#include <begin_vertex>\nvec3 windP=(modelMatrix*vec4(position,1.)).xyz;transformed.x+=sin(windP.z*1.4+uTime*.7)*.026*max(0.,windP.y-.18);",
              );
          };
          world.plantMaterials.push(o.material);
        }
      }
    });
    for (let i = 0; i < lamps.length; i++) {
      const [x, z, h] = lamps[i];
      const lamp = makeLamp(scene, x, z, h, i < 3 ? "column" : "street");
      if (i < 3)
        for (const child of [...lamp.children])
          if (!child.isSprite) lamp.remove(child);
    }
    const details = await loader.loadAsync("/assets/street-details.glb");
    scene.add(details.scene);
    details.scene.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
    const props = await loader.loadAsync("/assets/props.glb");
    scene.add(props.scene);
    props.scene.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        if (o.material.name.includes("illuminated glass")) {
          o.material.color.setHex(0xffd49a);
          o.material.emissive.setHex(0xffa84b);
          o.material.emissiveIntensity = 0.9;
        }
      }
    });
    obstacles.push(
      { type: "box", x: 16, z: 8, w: 0.8, d: 0.5 },
      { type: "circle", x: 2.8, z: -2.1, r: 0.35 },
    );
    const bark = await tl.loadAsync("/assets/tree-bark.png");
    bark.colorSpace = THREE.SRGBColorSpace;
    bark.wrapS = bark.wrapT = THREE.RepeatWrapping;
    bark.flipY = false;
    bark.anisotropy = 8;
    const plaster = await tl.loadAsync("/assets/ochre-plaster.png");
    plaster.colorSpace = THREE.SRGBColorSpace;
    plaster.wrapS = plaster.wrapT = THREE.RepeatWrapping;
    plaster.flipY = false;
    plaster.anisotropy = 8;
    const [surroundings, streets, aprons, architecture, cosy, cosyObstacles, treeAsset, courtyard] = await Promise.all([
      loader.loadAsync("/assets/surroundings-no-gate.glb"),
      loader.loadAsync("/assets/streets.glb"),
      loader.loadAsync("/assets/pavement-joins.glb"),
      loader.loadAsync("/assets/architecture-web.glb"),
      loader.loadAsync("/assets/cosy-street-finish.glb"),
      fetch("/assets/cosy-street-obstacles.json").then(r => r.json()),
      loader.loadAsync("/assets/trees-polish.glb"),
      loader.loadAsync("/assets/courtyard-edge.glb"),
    ]);
    // Replace entire old frontages, including their obsolete shop fittings.
    const obsolete = [];
    for (const root of [env.scene, surroundings.scene]) root.traverse(o => {
      if (/^Building_(North|West)_|^Park_Gate|^Tree_[0-3]_Bark$/.test(o.name)) obsolete.push(o);
    });
    obsolete.forEach(o => o.removeFromParent());
    env.scene.add(surroundings.scene, streets.scene, aprons.scene, architecture.scene, cosy.scene, treeAsset.scene, courtyard.scene);
    for (const o of cosyObstacles) obstacles.push({ type: "circle", x: o.x, z: o.z, r: o.radius, name: o.name });
    // A solid row follows the modeled work barrier at the end of the arrival street.
    for(let lateral=-4.1;lateral<=4.1;lateral+=.42) {
      const x=-.7933533403*41.5+.608761429*lateral;
      const z=-.608761429*41.5-.7933533403*lateral;
      obstacles.push({type:"circle",x,z,r:.25,name:"street works boundary"});
    }
    aprons.scene.traverse((o) => {
      if (!o.isMesh) return;
      o.material.map.wrapS = o.material.map.wrapT = THREE.RepeatWrapping;
      o.material.map.anisotropy = 8;
      o.material.map.colorSpace = THREE.SRGBColorSpace;
      o.material.bumpMap = o.material.map;
      o.material.bumpScale = 0.0018;
      o.material.userData.wetStrength = 0.13;
      world.addGroundShader(o.material);
      world.reflectionSurfaces.push(o);
    });
    streets.scene.traverse((o) => {
      if (!o.isMesh) return;
      const m = o.material;
      if (m.map) {
        m.map.wrapS = m.map.wrapT = THREE.RepeatWrapping;
        m.map.anisotropy = 8;
        m.map.colorSpace = THREE.LinearSRGBColorSpace;
      }
      if (m.name === "Street_Asphalt") {
        m.map = asphalt.clone();
        m.map.colorSpace = THREE.SRGBColorSpace;
        m.map.wrapS = m.map.wrapT = THREE.RepeatWrapping;
        m.map.repeat.set(0.85 / 3.1, 0.85 / 3.1);
        m.map.anisotropy = 8;
      }
      if (m.name === "Street_Sidewalk") {
        m.map = granite.clone();
        m.map.colorSpace = THREE.SRGBColorSpace;
        m.map.wrapS = m.map.wrapT = THREE.RepeatWrapping;
        m.map.repeat.set(.85/.32,.85/.32);
        m.map.anisotropy = 8;
      }
      if (/Street_Asphalt|Street_Sidewalk/.test(m.name)) {
        m.bumpMap = m.map;
        m.bumpScale = m.name === "Street_Asphalt" ? 0.004 : 0.0015;
        m.color.setScalar(m.name === "Street_Asphalt" ? 1.2 : 0.85);
        m.userData.wetStrength = m.name === "Street_Asphalt" ? 0.48 : 0.16;
        world.addGroundShader(m);
        world.reflectionSurfaces.push(o);
      }
    });
    const carAsset = await loader.loadAsync("/assets/parked-car-finish.glb");
    for (const placement of parkedCars) {
      const car = carAsset.scene.clone(true);
      car.name = "Parked unoccupied hatchback";
      car.position.set(placement.x, 0, placement.z);
      car.rotation.y = placement.yaw;
      for (const offset of [-1.1, 0, 1.1]) obstacles.push({type:"circle",x:placement.x+Math.sin(placement.yaw)*offset,z:placement.z+Math.cos(placement.yaw)*offset,r:.82,name:"parked car"});
      car.traverse((o) => {
        if (!o.isMesh) return;
        o.castShadow = o.receiveShadow = true;
        if (o.material.name === "CarPaint") {
          o.material = o.material.clone();
          o.material.color.setHex(placement.color);
          o.material.roughness = 0.42;
          o.material.metalness = 0.38;
          o.material.envMapIntensity = 0.50;
          o.material.clearcoat = 0.14;
          o.material.clearcoatRoughness = 0.36;
        }
        if (o.material.name === "Car inset tinted glass") {
          o.material = o.material.clone();
          o.material.envMapIntensity = .24;
          o.material.roughness = .30;
          o.material.metalness = 0;
          o.material.opacity = .38;
          o.material.onBeforeCompile = shader => {
            shader.fragmentShader=shader.fragmentShader.replace("#include <lights_fragment_end>","#include <lights_fragment_end>\nreflectedLight.directSpecular*=.45;reflectedLight.indirectSpecular*=.65;");
          };
          o.material.customProgramCacheKey=()=>"weathered-tinted-car-glass-v1";
        }
      });
      scene.add(car);
    }
    scene.add(env.scene);
    env.scene.traverse((o) => {
      if (o.isMesh) {
        // Replace the repeated atlas with separately authored wall sections.
        if (o.material.name === "Graffiti_Mural") {
          o.visible = false;
          return;
        }
        if (o.material.name === "Window_Lit") {
          o.material = new THREE.MeshBasicMaterial({
            color: 0xffbc65,
            toneMapped: false,
            vertexColors: true,
          });
          o.material.name = "Warm_Window_Interior";
        }
        if (o.material.name === "Window_Dim") {
          o.material = new THREE.MeshBasicMaterial({ color: 0x998069, vertexColors: true });
          o.material.name = "Dim_Window_Interior";
        }
        o.castShadow = true;
        o.receiveShadow = true;
        if (/Decal|WindowFilm/.test(o.material.name)) {
          o.castShadow = false;
          o.material.depthWrite = false;
        }
        if (o.name.startsWith("Building_")) {
          const groupName = o.name.includes("StreetContinuation")
            ? o.name.split("_").slice(0, 3).join("_")
            : o.name.split("_").slice(0, 2).join("_");
          if (!buildingOccluders.has(groupName))
            buildingOccluders.set(groupName, {
              meshes: [],
              walls: [],
              opacity: 1,
              target: 1,
            });
          const group = buildingOccluders.get(groupName);
          o.material = o.material.clone();
          o.material.forceSinglePass = true;
          o.userData.buildingBaseOpacity = o.material.opacity;
          o.userData.buildingBaseTransparent = o.material.transparent;
          o.userData.buildingBaseDepthWrite = o.material.depthWrite;
          group.meshes.push(o);
          if (/Plaster|Roof_Slate|Cosy_Lime|Cosy_RoseRustication|Cosy_Terracotta/.test(o.material.name)) {
            o.material.side = THREE.DoubleSide;
            group.walls.push(o);
          }
        }
        if (o.name.startsWith("Tree_")) {
          o.material = o.material.clone();
          o.material.transparent = true;
          o.userData.fadeTarget = 1;
          occluders.push(o);
        }
        if (o.material) {
          const mats = Array.isArray(o.material) ? o.material : [o.material];
          for (const m of mats) {
            m.envMapIntensity = 0.32;
            if (m.name === "Bark") {
              m.map = bark;
              m.bumpMap = bark;
              m.bumpScale = 0.035;
              m.color.setHex(0xb7ada2);
              m.roughness = 1;
            }
            if (m.name.startsWith("Plaster_")) {
              m.map = plaster;
              m.color.setHex(m.name === "Plaster_Ochre" ? 0xffffff : 0xc9bbb1);
              m.bumpMap = plaster;
              m.bumpScale = 0.075;
              m.roughness = 0.94;
            } else if (m.name.startsWith("Cosy_") && /Lime|RoseRustication|PaleLimestone|StoneBase/.test(m.name)) {
              m.bumpMap = m.map;
              m.bumpScale = .003;
              m.roughness = .94;
            } else if (m.name.includes("Stone")) {
              m.bumpMap = world.noise;
              m.bumpScale = 0.045;
              m.roughness = 0.88;
            }
            if (m.name.toLowerCase().includes("window")) {
              m.envMapIntensity = 0.85;
            }
          }
        }
      }
    });
    const heroMap = await tl.loadAsync(
      "/assets/graffiti-leget-bois-readable.png",
    );
    heroMap.colorSpace = THREE.SRGBColorSpace;
    heroMap.anisotropy = 8;
    const heroMural = new THREE.Mesh(
      new THREE.PlaneGeometry(7.8, 2.2),
      new THREE.MeshStandardMaterial({
        map: heroMap,
        color: 0xffffff,
        emissive: 0xc9af89,
        emissiveMap: heroMap,
        emissiveIntensity: 0.57,
        roughness: 0.92,
      }),
    );
    heroMural.name = "Hero_LEGET_BOIS";
    heroMural.rotation.y = -Math.PI / 2;
    heroMural.position.set(22.49, 1.3, -13.2);
    heroMural.receiveShadow = true;
    scene.add(heroMural);
    const supportingMurals = await Promise.all(
      ["palestina", "gaza", "mollan"].map(async (name) => {
        const map = await tl.loadAsync(`/assets/graffiti-${name}.png`);
        map.colorSpace = THREE.SRGBColorSpace;
        map.anisotropy = 8;
        return new THREE.MeshStandardMaterial({
          name: `Painted_${name}`, map, color: 0xc9c0b3,
          roughness: 0.96, emissive: 0xa49882, emissiveMap: map,
          emissiveIntensity: name === "mollan" ? 0.12 : 0.21,
        });
      }),
    );
    // Independent, smaller works sit inside the brick piers. LEGET BOIS retains
    // the widest panel and its own warm wall light along the park wall.
    for (const [z, art, width, height] of [
      [-21.5, 0, 4.25, 1.82], [-26.5, 2, 4.25, 1.72],
      [-31, 2, 3.1, 1.48], [-6, 2, 4.3, 1.72], [-0.5, 1, 4.25, 1.82],
      [4.5, 2, 4.25, 1.72], [9.5, 0, 4.25, 1.70],
      [14.5, 2, 4.25, 1.60], [19.5, 1, 4.25, 1.75],
    ]) {
      const panel = new THREE.Mesh(new THREE.PlaneGeometry(width, height), supportingMurals[art]);
      panel.name = `Mural_${["Palestina", "Gaza", "Mollan"][art]}_${z}`;
      panel.rotation.y = -Math.PI / 2;
      panel.position.set(22.725, 1.28, z);
      panel.receiveShadow = true;
      scene.add(panel);
    }

    const wallWash = new THREE.SpotLight(0xffd098, 65, 12, 0.72, 0.8, 2);
    wallWash.position.set(20.5, 4.5, -13.2);
    wallWash.target.position.set(23, 1.2, -13.2);
    scene.add(wallWash, wallWash.target);
    const cols = Array.isArray(collisionData)
      ? collisionData
      : collisionData.colliders || collisionData.collisions || [];
    for (const o of cols) {
      if (o.type === "circle")
        obstacles.push({ type: "circle", x: o.x, z: o.z, r: o.r ?? o.radius });
      if (o.type === "box" || o.type === "arc") obstacles.push(o);
    }
    obstacles.push({
      type: "circle",
      x: npcPosition.x,
      z: npcPosition.z,
      r: 0.55,
    });
    player = p.scene;
    npc = n.scene;
    scene.add(player, npc);
    player.position.copy(playerPosition);
    npc.position.copy(npcPosition);
    player.rotation.y = .918;
    npc.rotation.y = 0.1;
    const pedestrianAssets = await Promise.all([loader.loadAsync("/assets/pedestrian-a-refined.glb"), loader.loadAsync("/assets/pedestrian-b-refined.glb")]);
    pedestrians = createPedestrians(pedestrianAssets.map(a => a.scene), scene, obstacles);
    const characters = [player, npc, ...pedestrians.roots];
    const clothTexture = await tl.loadAsync("/assets/cloth-canvas.png");
    clothTexture.wrapS = clothTexture.wrapT = THREE.RepeatWrapping;
    clothTexture.anisotropy = 8;
    clothTexture.repeat.set(0.25, 0.25);
    const awningWeave=clothTexture.clone();awningWeave.repeat.set(2,2);
    env.scene.traverse(o=>{
      if(o.isMesh && /Cosy .*canvas/.test(o.material.name)) {
        o.material.bumpMap=awningWeave;o.material.bumpScale=.0025;o.material.roughness=1;
      }
    });
    for (const root of characters)
      root.traverse((o) => {
        if (o.isMesh) {
          o.castShadow = true;
          o.receiveShadow = true;
          if (o.isSkinnedMesh) o.frustumCulled = false;
          const ms = Array.isArray(o.material) ? o.material : [o.material];
          ms.forEach((m) => {
            m.envMapIntensity = 0.4;
            if (m.name === "Washed crimson jacket" && !m.userData.pigmentAdjusted) {
              m.color.multiplyScalar(0.77);
              m.userData.pigmentAdjusted = true;
            }
            if (/cloth|canvas|cotton|denim|jacket/i.test(m.name)) {
              if (!m.userData.weaveApplied) {
                m.map = clothTexture;
                m.color.multiplyScalar(1.65);
                m.userData.weaveApplied = true;
              }
              m.bumpMap = clothTexture;
              m.bumpScale = 0.004;
              m.roughness = 0.9;
            }
          });
        }
      });
    // Character grounding remains readable without updating the large static shadow map.
    const shadowCanvas = document.createElement("canvas");
    shadowCanvas.width = shadowCanvas.height = 64;
    const ctx = shadowCanvas.getContext("2d"),
      g = ctx.createRadialGradient(32, 32, 4, 32, 32, 32);
    g.addColorStop(0, "rgba(0,0,0,.65)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 64, 64);
    const sm = new THREE.MeshBasicMaterial({
      map: new THREE.CanvasTexture(shadowCanvas),
      transparent: true,
      depthWrite: false,
    });
    for (const root of characters) {
      const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.1), sm);
      shadow.rotation.x = -Math.PI / 2;
      shadow.position.y = 0.018;
      root.add(shadow);
    }
    await renderer.compileAsync(scene, camera);
    const fadingMaterials = [...buildingOccluders.values()].flatMap(g => g.meshes.map(o => o.material));
    const originalTransparency = fadingMaterials.map(m => m.transparent);
    fadingMaterials.forEach(m => { m.transparent = true; });
    await renderer.compileAsync(scene, camera);
    fadingMaterials.forEach((m,i) => { m.transparent = originalTransparency[i]; });
    // Bake static shadows once, exclude moving characters from the map to avoid stationary ghosts.
    player.traverse((o) => {
      if (o.isMesh) o.castShadow = false;
    });
    npc.traverse((o) => {
      if (o.isMesh) o.castShadow = false;
    });
    renderer.shadowMap.needsUpdate = true;
    // Capture the actual finished neighborhood once for inexpensive wet-surface reflections.
    characters.forEach(root => { root.visible = false; });
    const cubeTarget = new THREE.WebGLCubeRenderTarget(256, {
      type: THREE.HalfFloatType,
    });
    const cubeCamera = new THREE.CubeCamera(0.2, 140, cubeTarget);
    cubeCamera.position.set(0, 1.2, 0);
    cubeCamera.update(renderer, scene);
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromCubemap(cubeTarget.texture).texture;
    pmrem.dispose();
    cubeTarget.dispose();
    characters.forEach(root => { root.visible = true; });
    scene.traverse((o) => {
      if (o.isMesh) o.castShadow = false;
    });
    for (const root of characters)
      root.traverse((o) => {
        if (o.isMesh && !o.material.transparent) o.castShadow = true;
      });
    renderer.shadowMap.autoUpdate = true;
    ready = true;
    updateCamera(1);
    nightBloom.render(scene, camera);
    $("loading").style.opacity = "0";
    setTimeout(() => ($("loading").hidden = true), 850);
    canvas.focus();
    window.__game.ready = true;
  } catch (e) {
    console.error(e);
    $("load-status").hidden = false;
    $("load-status").textContent =
      "Kunde inte ladda kvarteret. Försök ladda om sidan.";
    window.__game.error = String(e);
  }
}
function updateCamera(dt) {
  const t = 1 - Math.exp(-dt * 10);
  yaw += (targetYaw - yaw) * t;
  pitch += (targetPitch - pitch) * t;
  distance += (targetDistance - distance) * t;
  const target = playerPosition.clone().add(new THREE.Vector3(0, 0.85, 0));
  camera.position.set(
    target.x + Math.sin(yaw) * Math.cos(pitch) * distance,
    target.y + Math.sin(pitch) * distance,
    target.z + Math.cos(yaw) * Math.cos(pitch) * distance,
  );
  camera.lookAt(target);
}
const dialogue = [
  [
    "BIG BLACK",
    "Du hittade högtalaren! Jag trodde den hade flyttat till Berlin.",
  ],
  ["DU", "Den stod på Möllan och spelade samma låt. I sex timmar."],
  ["BIG BLACK", "Det är ingen spellista. Det är ett koncept."],
  ["BIG BLACK", "Här. 250 spänn. Nästa gång hyr jag en tyst högtalare."],
];
function interact() {
  if (!ready) return;
  if (dialogueIndex >= 0) {
    dialogueIndex++;
    if (dialogueIndex >= dialogue.length) {
      closeDialogue();
      if (!completed) {
        completed = true;
        $("objective").textContent = "Högtalaren är hemma. Natten är din.";
        $("money").textContent = "3 650 kr";
        $("toast").hidden = false;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => ($("toast").hidden = true), 5500);
      }
      return;
    }
    showLine();
    return;
  }
  if (playerPosition.distanceTo(npcPosition) < 2.7) {
    keys.clear();
    if (completed) {
      $("speaker").textContent = "BIG BLACK";
      $("line").textContent =
        "Du står på gästlistan. Den sitter på kylskåpet, under elräkningen.";
      $("next").querySelector("span").textContent = "Vi ses";
      dialogueIndex = dialogue.length - 1;
      $("dialogue").hidden = false;
    } else {
      dialogueIndex = 0;
      showLine();
    }
  }
}
function showLine() {
  $("dialogue").hidden = false;
  $("speaker").textContent = dialogue[dialogueIndex][0];
  $("line").textContent = dialogue[dialogueIndex][1];
  $("next").querySelector("span").textContent =
    dialogueIndex === dialogue.length - 1 ? "Tack, vi ses" : "Fortsätt";
  $("nearby").hidden = true;
}
function closeDialogue() {
  dialogueIndex = -1;
  $("dialogue").hidden = true;
  canvas.focus();
}
$("next").onclick = interact;
window.addEventListener("keydown", (e) => {
  if (
    [
      "ArrowUp",
      "ArrowDown",
      "ArrowLeft",
      "ArrowRight",
      "Space",
      "KeyW",
      "KeyA",
      "KeyS",
      "KeyD",
    ].includes(e.code)
  )
    e.preventDefault();
  if (e.repeat && ["KeyE", "KeyP"].includes(e.code)) return;
  if (e.code === "KeyE" || (e.code === "Enter" && dialogueIndex >= 0))
    interact();
  if (e.code === "Escape") {
    closeDialogue();
  }
  if (e.code === "KeyR") {
    targetYaw = CAMERA.yaw;
    targetPitch = CAMERA.pitch;
    targetDistance = CAMERA.distance;
  }
  if (e.code === "KeyP") $("perf").hidden = !$("perf").hidden;
  keys.add(e.code);
});
window.addEventListener("keyup", (e) => keys.delete(e.code));
window.addEventListener("blur", () => keys.clear());
document.addEventListener("visibilitychange", () => {
  keys.clear();
  clock.getDelta();
});
let dragging = false,
  lastX = 0,
  lastY = 0;
canvas.addEventListener("pointerdown", (e) => {
  if (e.button !== 0 && e.button !== 2) return;
  dragging = true;
  lastX = e.clientX;
  lastY = e.clientY;
  canvas.setPointerCapture(e.pointerId);
  canvas.style.cursor = "grabbing";
  canvas.focus();
});
canvas.addEventListener("pointermove", (e) => {
  if (!dragging) return;
  targetYaw -= (e.clientX - lastX) * 0.006;
  targetPitch = THREE.MathUtils.clamp(
    targetPitch + (e.clientY - lastY) * 0.002,
    CAMERA.minPitch,
    CAMERA.maxPitch,
  );
  lastX = e.clientX;
  lastY = e.clientY;
});
canvas.addEventListener("pointerup", () => {
  dragging = false;
  canvas.style.cursor = "grab";
});
canvas.addEventListener("lostpointercapture", () => {
  dragging = false;
  canvas.style.cursor = "grab";
});
canvas.addEventListener("contextmenu", (e) => e.preventDefault());
canvas.addEventListener(
  "wheel",
  (e) => {
    e.preventDefault();
    targetDistance = THREE.MathUtils.clamp(
      targetDistance * Math.exp(e.deltaY * 0.001),
      CAMERA.min,
      CAMERA.max,
    );
  },
  { passive: false },
);
window.addEventListener("resize", () => {
  renderer.setPixelRatio(screenPixelRatio());
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight, false);
});
let renderingPaused = false, gpuProfiling = false;
let nextFrame = performance.now();
const timerExtension = gl.getExtension("EXT_disjoint_timer_query_webgl2");
const gpuQueries = [], gpuTimes = [], cpuTimes = [];
function beginGpuTiming() {
  if (!timerExtension || !gpuProfiling) return null;
  while (gpuQueries.length && gl.getQueryParameter(gpuQueries[0], gl.QUERY_RESULT_AVAILABLE)) {
    const q = gpuQueries.shift();
    if (!gl.getParameter(timerExtension.GPU_DISJOINT_EXT)) {
      gpuTimes.push(gl.getQueryParameter(q, gl.QUERY_RESULT) / 1e6);
      if (gpuTimes.length > 180) gpuTimes.shift();
    }
    gl.deleteQuery(q);
  }
  if (gpuQueries.length > 5) return null;
  const q = gl.createQuery();
  gl.beginQuery(timerExtension.TIME_ELAPSED_EXT, q);
  return q;
}
let lastFrame = performance.now(),
  frameHistory = [],
  measure = null,
  elapsed = 0;
function tick(now) {
  requestAnimationFrame(tick);
  if (document.hidden || renderingPaused) {
    clock.getDelta();
    lastFrame = nextFrame = now;
    return;
  }
  // Keep an absolute presentation cadence. Re-anchoring on each slightly late
  // RAF accumulates drift and unnecessarily skips a whole 60 Hz refresh.
  if (frameLimit && now < nextFrame - Math.min(8, 250 / frameLimit)) return;
  if (frameLimit) {
    const interval = 1000 / frameLimit;
    nextFrame += interval;
    if (now - nextFrame > interval) nextFrame = now;
  } else nextFrame = now;
  const cpuStart = performance.now();
  const raw = now - lastFrame;
  lastFrame = now;
  const dt = Math.min(clock.getDelta(), 0.05);
  elapsed += dt;
  if (ready) {
    const input = cameraRelativeInput(keys, yaw),
      moving = input.moving && dialogueIndex < 0;
    let moved = false;
    if (moving) {
      const running = keys.has("ShiftLeft") || keys.has("ShiftRight");
      const speed = running ? 3.1 : 1.8;
      player.userData.running = running;
      player.userData.strideLength = running ? 1.55 : 1.02;
      const prev = playerPosition.clone();
      const blocked = moveWithCollision(
        playerPosition,
        input.x * speed * dt,
        input.z * speed * dt,
        obstacles,
      );
      moved = prev.distanceToSquared(playerPosition) > 0.000001;
      if (
        blocked &&
        (playerPosition.x / 19) ** 2 + (playerPosition.z / 22) ** 2 > 0.95
      ) {
        $("boundary").hidden = false;
        clearTimeout(boundaryTimer);
        boundaryTimer = setTimeout(() => ($("boundary").hidden = true), 1800);
      }
      const angle = Math.atan2(input.x, input.z);
      player.rotation.y +=
        Math.atan2(
          Math.sin(angle - player.rotation.y),
          Math.cos(angle - player.rotation.y),
        ) *
        (1 - Math.exp(-dt * 14));
      walkPhase += prev.distanceTo(playerPosition) * Math.PI * 2 / player.userData.strideLength;
    }
    playerPosition.y = groundHeight(playerPosition.x, playerPosition.z);
    player.position.copy(playerPosition);
    animateCharacter(player, elapsed, moved, walkPhase, playerPosition.y, .43, dt);
    // Turn the full character toward the speaker, taking the shortest arc.
    // Retain his last facing direction once the conversation ends.
    if (dialogueIndex >= 0) {
      const facing = Math.atan2(playerPosition.x - npcPosition.x, playerPosition.z - npcPosition.z);
      npc.rotation.y += Math.atan2(Math.sin(facing - npc.rotation.y), Math.cos(facing - npc.rotation.y)) * (1 - Math.exp(-dt * 9));
    }
    npc.userData.talking = dialogueIndex >= 0;
    animateCharacter(npc, elapsed + 1, false, 0, npcPosition.y, .43, dt);
    pedestrians.update(dt, elapsed, playerPosition, (...args) => animateCharacter(...args, dt));
    world.plantMaterials?.forEach((m) => {
      if (m.userData.shader) m.userData.shader.uniforms.uTime.value = elapsed;
    });
    updateCamera(dt);
    world.stoneRoad.update(camera);
    const near = playerPosition.distanceTo(npcPosition) < 2.7;
    $("nearby").hidden = !near || dialogueIndex >= 0;
    characterLight.position
      .copy(playerPosition)
      .add(new THREE.Vector3(-4, 8, -3));
    characterLight.target.position.copy(playerPosition);
    characterLight.shadow.needsUpdate = true;
    occlusionTime += dt;
    if (occlusionTime > 0.12) {
      occlusionTime = 0;
      const aim = playerPosition.clone().add(new THREE.Vector3(0, 0.85, 0));
      const delta = aim.clone().sub(camera.position);
      cameraRay.set(camera.position, delta.clone().normalize());
      cameraRay.far = delta.length() - 0.6;
      const hits = new Set(cameraRay.intersectObjects(occluders, false).map((h) => h.object));
      // Check the body's vertical extent so a fork can't hide the centered
      // character merely because one thin ray passes between its branches.
      for (const height of [0.35, 1.35]) {
        const bodyAim = playerPosition.clone().add(new THREE.Vector3(0, height, 0));
        const bodyDelta = bodyAim.sub(camera.position);
        cameraRay.set(camera.position, bodyDelta.normalize());
        for (const hit of cameraRay.intersectObjects(occluders, false)) hits.add(hit.object);
      }
      cameraRay.set(camera.position, delta.clone().normalize());
      for (const o of occluders) o.userData.fadeTarget = hits.has(o) ? 0.12 : 1;
      for (const group of buildingOccluders.values()) {
        group.target = cameraRay.intersectObjects(group.walls, false).length
          ? 0
          : 1;
      }
    }
    for (const o of occluders) {
      o.material.opacity +=
        (o.userData.fadeTarget - o.material.opacity) * (1 - Math.exp(-dt * 8));
      o.material.depthWrite = o.material.opacity > 0.96;
    }
    for (const group of buildingOccluders.values()) {
      group.opacity += (group.target - group.opacity) * (1 - Math.exp(-dt * 9));
      for (const o of group.meshes) {
        o.material.opacity = group.opacity * o.userData.buildingBaseOpacity;
        o.material.transparent =
          o.userData.buildingBaseTransparent || group.opacity < 0.999;
        o.material.depthWrite =
          o.userData.buildingBaseDepthWrite && group.opacity > 0.96;
        o.visible = group.opacity > 0.01;
      }
    }
    renderer.info.reset();
    const gpuQuery = beginGpuTiming();
    wetReflection.render(renderer, scene, camera, world.reflectionSurfaces);
    nightBloom.render(scene, camera);
    if (gpuQuery) {
      gl.endQuery(timerExtension.TIME_ELAPSED_EXT);
      gpuQueries.push(gpuQuery);
    }
    cpuTimes.push(performance.now() - cpuStart);
    if (cpuTimes.length > 180) cpuTimes.shift();
    frameHistory.push(raw);
    if (frameHistory.length > 180) frameHistory.shift();
    if (measure && now >= measure.start) {
      measure.frames.push(raw);
      if (now - measure.start >= measure.duration) {
        measure.resolve(report(measure.frames));
        measure = null;
      }
    }
    if (
      !$("perf").hidden &&
      Math.floor(elapsed * 3) !== Math.floor((elapsed - dt) * 3)
    ) {
      const r = report(frameHistory);
      $("perf").textContent =
        `${r.fps} fps · ${r.p95} ms p95\n${r.drawCalls} draw calls · ${Math.round(r.triangles / 1000)}k tris\n${canvas.width} × ${canvas.height}`;
    }
  }
}
function report(frames) {
  const f = frames.filter((n) => n > 0 && n < 1000).sort((a, b) => a - b);
  const avg = f.reduce((a, b) => a + b, 0) / f.length;
  const q = (p) => +(f[Math.floor((f.length - 1) * p)] || 0).toFixed(2);
  return {
    frames: f.length,
    fps: +(1000 / avg).toFixed(2),
    meanMs: +avg.toFixed(2),
    cpuMeanMs: +(cpuTimes.reduce((a,b)=>a+b,0) / cpuTimes.length).toFixed(2),
    gpuMeanMs: gpuTimes.length ? +(gpuTimes.reduce((a,b)=>a+b,0) / gpuTimes.length).toFixed(2) : null,
    p50: q(0.5),
    p95: q(0.95),
    p99: q(0.99),
    frameLimit,
    overBudget: f.filter((x) => x > 1000 / (frameLimit || 60) + 2).length,
    over50ms: f.filter((x) => x > 50).length,
    over20ms: f.filter((x) => x > 20).length,
    over33ms: f.filter((x) => x > 33.4).length,
    drawCalls: renderer.info.render.calls,
    triangles: renderer.info.render.triangles,
    resolution: [canvas.width, canvas.height],
    pixelRatio: renderer.getPixelRatio(),
    renderer: renderer
      .getContext()
      .getParameter(
        renderer.getContext().getExtension("WEBGL_debug_renderer_info")
          ?.UNMASKED_RENDERER_WEBGL || renderer.getContext().RENDERER,
      ),
  };
}
window.__game = {
  ready: false,
  scene,
  camera,
  renderer,
  playerPosition,
  npcPosition,
  get pedestrians() { return pedestrians?.states; },
  obstacles,
  keys,
  get state() {
    return {
      ready,
      position: playerPosition.toArray(),
      yaw,
      pitch,
      distance,
      dialogueIndex,
      completed,
      near: playerPosition.distanceTo(npcPosition) < 2.7,
    };
  },
  stats: () => report(frameHistory),
  setPaused: (value) => { renderingPaused = Boolean(value); },
  profileGPU: (value) => { gpuProfiling = Boolean(value); gpuTimes.length = 0; },
  setFrameLimit: (fps) => {
    frameLimit = fps;
    nextFrame = performance.now();
    frameHistory.length = 0;
  },
  get frameLimit() {
    return frameLimit;
  },
  benchmark: (seconds = 30) =>
    new Promise((resolve) => {
      measure = {
        start: performance.now() + 1000,
        duration: seconds * 1000,
        frames: [],
        resolve,
      };
    }),
  setResolution: (w, h) => {
    renderer.setPixelRatio(1);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  },
  setCamera: (y, p, d) => {
    targetYaw = y;
    targetPitch = THREE.MathUtils.clamp(p, CAMERA.minPitch, CAMERA.maxPitch);
    targetDistance = THREE.MathUtils.clamp(d, CAMERA.min, CAMERA.max);
  },
  teleport: (x, z) => {
    if (canOccupy(x, z, obstacles)) {
      playerPosition.x = x;
      playerPosition.z = z;
      return true;
    }
    return false;
  },
};
requestAnimationFrame(tick);
init();
