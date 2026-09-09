import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { insideBorderBed } from "./collision.js";
import layout from "./layout.json";
import { streetPoint } from "./neighbourhood.js";
export const lamps = layout.lamps;
export const parkedCars = layout.parkedCars;
export const beds = layout.beds;
export const borderBeds = layout.borderBeds;
export const obstacles = [];
let seed = 21091;
export function random() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}
function canvasTexture(w, h, draw) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
export function noiseTexture() {
  const t = canvasTexture(256, 256, (ctx, w, h) => {
    const im = ctx.createImageData(w, h);
    for (let i = 0; i < im.data.length; i += 4) {
      const n = 90 + random() * 110;
      im.data[i] = im.data[i + 1] = im.data[i + 2] = n;
      im.data[i + 3] = 255;
    }
    ctx.putImageData(im, 0, 0);
  });
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(6, 6);
  return t;
}
export function makeEnvironment(renderer) {
  const s = new THREE.Scene();
  const sky = new THREE.Mesh(
    new THREE.SphereGeometry(100, 32, 16),
    new THREE.ShaderMaterial({
      side: THREE.BackSide,
      uniforms: {},
      vertexShader:
        "varying vec3 vP;void main(){vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
      fragmentShader:
        "varying vec3 vP;void main(){float y=normalize(vP).y;vec3 c=mix(vec3(.014,.023,.029),vec3(.10,.14,.17),smoothstep(-.1,.6,y));gl_FragColor=vec4(c,1.);}",
    }),
  );
  s.add(sky);
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    const m = new THREE.Mesh(
      new THREE.PlaneGeometry(5 + (i % 3) * 2, 10),
      new THREE.MeshBasicMaterial({ color: i % 3 === 0 ? 0x6e90a1 : 0xffbd63 }),
    );
    m.position.set(Math.sin(a) * 40, 4, Math.cos(a) * 40);
    m.lookAt(0, 3, 0);
    s.add(m);
  }
  const pm = new THREE.PMREMGenerator(renderer);
  const out = pm.fromScene(s, 0.08);
  pm.dispose();
  s.traverse((o) => {
    o.geometry?.dispose();
    o.material?.dispose();
  });
  return out.texture;
}
export function buildWorld(scene, textures) {
  const noise = noiseTexture();
  const stoneMap = textures.cobble;
  stoneMap.wrapS = stoneMap.wrapT = THREE.RepeatWrapping;
  stoneMap.anisotropy = 8;
  stoneMap.colorSpace = THREE.SRGBColorSpace;
  // Bake static lamp irradiance once into a world-space texture. Rendering needs one texture lookup.
  const lightMap = canvasTexture(1024, 1024, (ctx, w, h) => {
    ctx.fillStyle = "#050909";
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    for (const [x, z, height, power] of lamps) {
      const px = ((x + 65) / 130) * w,
        py = ((65 - z) / 130) * h;
      const r = ((height * 2.7) / 130) * w;
      let g = ctx.createRadialGradient(px, py, 0, px, py, r);
      g.addColorStop(0, `rgba(215,137,52,${0.48 * power})`);
      g.addColorStop(0.25, `rgba(187,104,30,${0.31 * power})`);
      g.addColorStop(0.6, "rgba(115,64,25,.10)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.fillRect(px - r, py - r, 2 * r, 2 * r);
    }
  });
  const groundMat = new THREE.MeshStandardMaterial({
    map: stoneMap,
    bumpMap: stoneMap,
    bumpScale: 0.035,
    roughness: 0.23,
    metalness: 0.2,
    color: 0xb0bdca,
    envMapIntensity: 0.8,
  });
  const reflectionSurfaces = [];
  const addGroundShader = (mat) => {
    mat.onBeforeCompile = (shader) => {
      shader.uniforms.bakedGround = { value: textures.lightMap || lightMap };
      shader.uniforms.bakedIntensity = { value: 1.15 };
      shader.uniforms.wetStrength = { value: mat.userData.wetStrength ?? 1 };
      shader.uniforms.wetReflection = { value: textures.wetReflection.texture };
      shader.uniforms.wetMatrix = { value: textures.wetReflection.matrix };
      mat.userData.shader = shader;
      shader.vertexShader = shader.vertexShader
        .replace(
          "#include <common>",
          "#include <common>\nvarying vec3 worldGround;",
        )
        .replace(
          "#include <worldpos_vertex>",
          `#include <worldpos_vertex>
vec4 groundPosition=vec4(transformed,1.);
#ifdef USE_INSTANCING
groundPosition=instanceMatrix*groundPosition;
#endif
worldGround=(modelMatrix*groundPosition).xyz;`,
        );
      shader.fragmentShader = shader.fragmentShader
        .replace(
          "#include <shadowmap_pars_fragment>",
          "#include <shadowmap_pars_fragment>\n#include <shadowmask_pars_fragment>",
        )
        .replace(
          "#include <common>",
          "#include <common>\nuniform sampler2D bakedGround;uniform float bakedIntensity;uniform float wetStrength;uniform sampler2D wetReflection;uniform mat4 wetMatrix;varying vec3 worldGround;",
        );
      shader.fragmentShader = shader.fragmentShader.replace(
        "#include <roughnessmap_fragment>",
        `#include <roughnessmap_fragment>
   float wetPatch=sin(worldGround.x*.49+sin(worldGround.z*.34))*sin(worldGround.z*.57+worldGround.x*.16);
   roughnessFactor=mix(.14,.55,smoothstep(-.3,.7,wetPatch));`,
      );
      shader.fragmentShader = shader.fragmentShader.replace(
        "#include <opaque_fragment>",
        `
   vec3 baked=texture2D(bakedGround,vec2((worldGround.x+65.)/130.,(65.-worldGround.z)/130.)).rgb;
   vec3 worldNormal=inverseTransformDirection(normal,viewMatrix);
   float stoneRelief=.60+.40*max(0.,worldNormal.y);
   outgoingLight=diffuseColor.rgb*(baked*mix(.5,1.,getShadowMask())+vec3(.035,.047,.062))*bakedIntensity*stoneRelief;
   vec4 projected=wetMatrix*vec4(worldGround,1.);
   vec2 reflectUV=projected.xy/projected.w;
   reflectUV+=worldNormal.xz*.012;
   reflectUV+=vec2(sin(worldGround.z*8.7+worldGround.x*1.3),sin(worldGround.x*7.7))*.0018;
   float blur=.0012+roughnessFactor*.004;
   vec3 reflection=texture2D(wetReflection,reflectUV).rgb*.4;
   reflection+=texture2D(wetReflection,reflectUV+vec2(blur,0.)).rgb*.15;
   reflection+=texture2D(wetReflection,reflectUV-vec2(blur,0.)).rgb*.15;
   reflection+=texture2D(wetReflection,reflectUV+vec2(0.,blur)).rgb*.15;
   reflection+=texture2D(wetReflection,reflectUV-vec2(0.,blur)).rgb*.15;
   float stone=dot(texture2D(map,vMapUv).rgb,vec3(.333));
   float stoneFace=smoothstep(.035,.17,stone);
   float puddle=.12+.78*smoothstep(-.1,.65,-wetPatch);
   float fresnel=.48+.8*pow(1.-max(0.,dot(worldNormal,normalize(cameraPosition-worldGround))),4.);
   float waterFilm=.62+.52*smoothstep(-.3,.6,sin(worldGround.x*17.+sin(worldGround.z*7.))*sin(worldGround.z*31.));
   float arrivalZone=(1.-smoothstep(6.,10.,length(worldGround.xz-vec2(-24.,-18.5))));
   float wornDry=1.-arrivalZone*.72*smoothstep(.12,.58,sin(worldGround.x*2.3+sin(worldGround.z*.85))*sin(worldGround.z*2.9));
   outgoingLight+=reflection*fresnel*puddle*(.18+stoneFace*.82)*wetStrength*waterFilm*wornDry;
   #include <opaque_fragment>`,
      );
    };
  };
  addGroundShader(groundMat);
  function surface(geo, mat, y) {
    const uv = geo.getAttribute("uv"),
      pos = geo.getAttribute("position");
    for (let i = 0; i < pos.count; i++)
      uv.setXY(i, pos.getX(i) / 3.1, pos.getY(i) / 3.1);
    const m = new THREE.Mesh(geo, mat);
    m.rotation.x = -Math.PI / 2;
    m.position.y = y;
    m.receiveShadow = true;
    m.renderOrder = 3;
    scene.add(m);
    reflectionSurfaces.push(m);
    return m;
  }
  const asphaltMat = groundMat.clone();
  textures.asphalt.colorSpace = THREE.SRGBColorSpace;
  textures.asphalt.wrapS = textures.asphalt.wrapT = THREE.RepeatWrapping;
  textures.asphalt.anisotropy = 8;
  asphaltMat.map = textures.asphalt;
  asphaltMat.bumpMap = textures.asphalt;
  asphaltMat.bumpScale = .006;
  asphaltMat.color.setHex(0xffffff);
  asphaltMat.userData.wetStrength = .08;
  addGroundShader(asphaltMat);
  surface(new THREE.PlaneGeometry(160, 160), asphaltMat, 0);
  // Cobbles follow the roundabout, with continuous radial courses.
  const roadPositions = [],
    roadUV = [],
    roadIndices = [];
  const ringSegments = 240;
  for (let ring = 0; ring < 2; ring++)
    for (let i = 0; i <= ringSegments; i++) {
      const a = (i / ringSegments) * Math.PI * 2;
      roadPositions.push(
        Math.sin(a) * (ring ? 20.2 : 11),
        0,
        Math.cos(a) * (ring ? 22.22 : 14),
      );
      roadUV.push((i / ringSegments) * 31 + .13*Math.sin(a*11) + .065*Math.sin(a*23),
        (ring ? 2.85 : 0) + .11*Math.sin(a*7));
    }
  for (let i = 0; i < ringSegments; i++) {
    const a = i,
      b = i + 1,
      c = i + ringSegments + 1,
      d = c + 1;
    roadIndices.push(a, c, b, b, c, d);
  }
  const roadGeo = new THREE.BufferGeometry();
  roadGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(roadPositions, 3),
  );
  roadGeo.setAttribute("uv", new THREE.Float32BufferAttribute(roadUV, 2));
  roadGeo.setIndex(roadIndices);
  roadGeo.computeVertexNormals();
  const road = new THREE.Mesh(roadGeo, groundMat);
  road.position.y = 0.004;
  road.receiveShadow = true;
  road.renderOrder = 2;
  scene.add(road);
  reflectionSurfaces.push(road);
  const islandMat = groundMat.clone();
  islandMat.color.setHex(0xe0d6c0);
  islandMat.roughness = 0.43;
  islandMat.envMapIntensity = 0.38;
  addGroundShader(islandMat);
  const islandGeo = new THREE.CircleGeometry(1, 120);
  islandGeo.scale(11, 14, 1);
  // Narrow dark joints below individually chipped, uneven granite setts.
  const jointMat = islandMat.clone();
  jointMat.color.setHex(0x95998d);
  jointMat.map = textures.granite;
  jointMat.bumpMap = null;
  jointMat.userData.wetStrength = 0.1;
  addGroundShader(jointMat);
  // Settled grout rises in irregular patches, breaking continuous dark row seams.
  const settledJoints = new THREE.PlaneGeometry(22,28,88,112);
  const jp=settledJoints.attributes.position;
  for(let i=0;i<jp.count;i++) {
    const x=jp.getX(i),z=-jp.getY(i);
    const wear=Math.sin(x*2.2+Math.sin(z*1.3))*Math.sin(z*2.7+x*.5);
    jp.setZ(i,.0085*THREE.MathUtils.smoothstep(wear,-.4,.55));
  }
  const ji=settledJoints.index.array, retained=[];
  for(let i=0;i<ji.length;i+=3) {
    if([ji[i],ji[i+1],ji[i+2]].every(j=>(jp.getX(j)/10.94)**2+(jp.getY(j)/13.94)**2<1)) retained.push(ji[i],ji[i+1],ji[i+2]);
  }
  settledJoints.setIndex(retained);settledJoints.computeVertexNormals();
  surface(settledJoints,jointMat,.138).renderOrder=2;
  islandGeo.dispose();
  textures.granite.colorSpace = THREE.SRGBColorSpace;
  textures.granite.wrapS = textures.granite.wrapT = THREE.RepeatWrapping;
  textures.granite.anisotropy = 8;
  const paverMat = new THREE.MeshStandardMaterial({
    map: textures.granite,
    bumpMap: textures.granite,
    bumpScale: 0.0025,
    color: 0xd4d2c8,
    roughness: 0.65,
    metalness: 0.08,
  });
  paverMat.userData.wetStrength = 0.65;
  addGroundShader(paverMat);
  const batches = Array.from({ length: 6 }, () => []);
  let row = 0;
  for (let z = -13.9; z < 13.9; z += 0.151, row++) {
    let x = -11 + (row % 2) * 0.125;
    while (x < 11) {
      const width = 0.253 * (0.82 + random() * 0.36);
      const xx = x + width / 2,
        zz = z + (random() - 0.5) * 0.01;
      x += width;
      if ((xx / 10.84) ** 2 + (zz / 13.83) ** 2 > 1) continue;
      if (borderBeds.some((b) => insideBorderBed(xx, zz, b, -0.06))) continue;
      if (
        beds.some((b) => {
          const dx = xx - b.x,
            dz = zz - b.z;
          const u = dx * Math.cos(b.angle) + dz * Math.sin(b.angle),
            v = -dx * Math.sin(b.angle) + dz * Math.cos(b.angle);
          const a = Math.atan2(v / b.rz, u / b.rx);
          const localRx = b.rx * (1 + 0.08 * Math.sin(a * 3));
          return (u / (localRx * 0.975)) ** 2 + (v / (b.rz * 0.975)) ** 2 < 1;
        })
      )
        continue;
      batches[Math.floor(random() * 6)].push([xx, zz, width / 0.253]);
    }
  }
  const sett = new THREE.Object3D();
  batches.forEach((positions, index) => {
    const model = textures.pavers.getObjectByName("Paver_" + index);
    const mesh = new THREE.InstancedMesh(
      model.geometry,
      paverMat,
      positions.length,
    );
    mesh.name = "Hand-set island granite " + index;
    positions.forEach(([x, z, width], i) => {
      sett.position.set(x, 0.139 + random() * 0.003, z);
      sett.rotation.set(
        (random() - 0.5) * 0.025,
        (random() - 0.5) * 0.018,
        (random() - 0.5) * 0.022,
      );
      sett.scale.set(width * 1.025, 0.86 + random() * 0.3, 1.04 + random() * 0.06);
      sett.updateMatrix();
      mesh.setMatrixAt(i, sett.matrix);
      mesh.setColorAt(i, new THREE.Color().setScalar(0.8 + random() * 0.2));
    });
    mesh.receiveShadow = true;
    mesh.renderOrder = 1;
    scene.add(mesh);
    reflectionSurfaces.push(mesh);
  });
  const pavement = groundMat.clone();
  pavement.color.setHex(0x999d93);
  pavement.roughness = 0.65;
  addGroundShader(pavement);
  // Curved granite curb: individual bevelled, imperfectly toned blocks, merged via instancing.
  const curbGeo = textures.pavers.getObjectByName("CurbBlock").geometry;
  const curbMat = new THREE.MeshStandardMaterial({
    color: 0xb0afa0,
    map: textures.granite,
    bumpMap: textures.granite,
    bumpScale: 0.003,
    roughness: 0.64,
  });
  // Soft ground bounce on the vertical stone faces keeps the narrow curb
  // readable without flattening its top or adding another dynamic light.
  curbMat.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <emissivemap_fragment>",
      "#include <emissivemap_fragment>\nvec3 curbWorldNormal=inverseTransformDirection(normal,viewMatrix);\ntotalEmissiveRadiance+=vec3(.045,.044,.037)*(1.-abs(curbWorldNormal.y));",
    );
  };
  curbMat.customProgramCacheKey = () => "curb-ground-bounce-v2";
  const curbs = new THREE.InstancedMesh(curbGeo, curbMat, 140);
  curbs.name = "Individual island curb stones";
  const dummy = new THREE.Object3D();
  for (let i = 0; i < 140; i++) {
    const a = (i / 140) * Math.PI * 2;
    dummy.position.set(Math.sin(a) * 11, 0.11, Math.cos(a) * 14);
    dummy.rotation.y = Math.atan2(14 * Math.sin(a), 11 * Math.cos(a));
    dummy.scale.set(
      ((Math.hypot(11 * Math.cos(a), 14 * Math.sin(a)) * Math.PI * 2) / 140 -
        0.012) /
        0.57,
      1,
      1,
    );
    dummy.updateMatrix();
    curbs.setMatrixAt(i, dummy.matrix);
    curbs.setColorAt(i, new THREE.Color().setScalar(0.86 + random() * 0.16));
  }
  curbs.castShadow = true;
  // The narrow bevels are smaller than a static shadow texel; avoid self-shadow
  // striping while retaining the curb's cast contact shadow on the ground.
  curbs.receiveShadow = false;
  scene.add(curbs);
  // Solid masonry behind the segmented curb closes tiny through-gaps without
  // flattening the individually worn stones along its exposed edge.
  const foundation = new THREE.Mesh(
    new THREE.CylinderGeometry(1, 1, 0.18, 140, 1, true),
    new THREE.MeshStandardMaterial({color: 0x5b5b52, roughness: 1, side: THREE.DoubleSide}),
  );
  foundation.position.y = 0.065;
  foundation.scale.set(11.11, 1, 14.11);
  foundation.receiveShadow = true;
  scene.add(foundation);
  const innerFoundation = foundation.clone();
  innerFoundation.scale.set(10.895, 1, 13.895);
  scene.add(innerFoundation);
  const atStreetMouth = (a) => [4.058, 5.585].some((gap) =>
    Math.abs(Math.atan2(Math.sin(a-gap), Math.cos(a-gap))) < 0.18);
  const sidewalkVertices = [], sidewalkIndices = [];
  for (let i = 0; i < 256; i++) {
    const a = i * Math.PI * 2 / 256, b = (i+1) * Math.PI * 2 / 256;
    if (atStreetMouth((a+b)/2)) continue;
    const base = sidewalkVertices.length / 3;
    for (const [angle, radius] of [[a,20.2],[a,23.2],[b,23.2],[b,20.2]])
      sidewalkVertices.push(Math.sin(angle)*radius,-Math.cos(angle)*radius*1.1,0);
    sidewalkIndices.push(base,base+1,base+2,base,base+2,base+3);
  }
  const sidewalkGeo = new THREE.BufferGeometry();
  sidewalkGeo.setAttribute("position",new THREE.Float32BufferAttribute(sidewalkVertices,3));
  sidewalkGeo.setAttribute("uv",new THREE.Float32BufferAttribute(new Float32Array(sidewalkVertices.length/3*2),2));
  sidewalkGeo.setIndex(sidewalkIndices);sidewalkGeo.computeVertexNormals();
  pavement.map = textures.granite; pavement.bumpMap = textures.granite;
  pavement.color.setHex(0x555951);pavement.userData.wetStrength=0.06;
  surface(sidewalkGeo, pavement, 0.148);
  const slabMaterial = paverMat.clone();
  slabMaterial.color.setHex(0xbac0bb); slabMaterial.bumpScale = 0.0018;
  slabMaterial.userData.wetStrength = 0.18; addGroundShader(slabMaterial);
  const slabs = Array.from({length:6},()=>[]);
  for(let row=0;row<6;row++) {
    const radius=20.45+row*.5;
    const count=Math.round(Math.PI*2*radius*1.05/.60);
    for(let col=0;col<count;col++) {
      const a=(col+(row%2)*.5)*Math.PI*2/count;
      if(atStreetMouth(a)) continue;
      slabs[(col+row*3)%6].push({a,radius,width:Math.hypot(Math.cos(a),1.1*Math.sin(a))*radius*Math.PI*2/count-.012});
    }
  }
  slabs.forEach((batch,index)=>{
    const geometry=textures.pavers.getObjectByName("Paver_"+index).geometry.clone();
    const uv=geometry.attributes.uv;
    for(let i=0;i<uv.count;i++) uv.setXY(i,uv.getX(i)*32,uv.getY(i)*40);
    const mesh=new THREE.InstancedMesh(geometry,slabMaterial,batch.length);
    batch.forEach(({a,radius,width},i)=>{
      dummy.position.set(Math.sin(a)*radius,0.162,Math.cos(a)*radius*1.1);
      dummy.rotation.set(0,Math.atan2(1.1*Math.sin(a),Math.cos(a)),0);
      dummy.scale.set(width/.238,.5,.487/.135);
      dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);
      mesh.setColorAt(i,new THREE.Color().setScalar(.85+random()*.14));
    });
    mesh.name="Outer pavement slabs "+index;mesh.receiveShadow=true;
    scene.add(mesh);reflectionSurfaces.push(mesh);
  });
  textures.soil.colorSpace = THREE.SRGBColorSpace;
  textures.soil.wrapS = textures.soil.wrapT = THREE.RepeatWrapping;
  textures.soil.anisotropy = 8;
  textures.soil.repeat.set(1.6, 1.6);
  const soilMat = new THREE.MeshStandardMaterial({
    color: 0xada69a,
    map: textures.soil,
    bumpMap: textures.soil,
    bumpScale: 0.12,
    roughness: 1,
  });
  for (const b of borderBeds) {
    const shape = new THREE.Shape();
    const point = (a, outer) =>
      new THREE.Vector2(
        Math.sin(a) * (outer ? b.outerRx : b.innerRx),
        -Math.cos(a) * (outer ? b.outerRz : b.innerRz),
      );
    const n = 60;
    for (let i = 0; i <= n; i++) {
      const p = point(b.start + ((b.end - b.start) * i) / n, true);
      if (i === 0) shape.moveTo(p.x, p.y);
      else shape.lineTo(p.x, p.y);
    }
    let p = point(b.end, false);
    shape.lineTo(p.x, p.y);
    for (let i = n; i >= 0; i--) {
      const p = point(b.start + ((b.end - b.start) * i) / n, false);
      shape.lineTo(p.x, p.y);
    }
    shape.closePath();
    const soil = surface(new THREE.ExtrudeGeometry(shape, {depth: 0.072, bevelEnabled: false, steps: 1}), soilMat, 0.108);
    soil.renderOrder = 1;
    obstacles.push({ type: "border", ...b });
    const edging = new THREE.InstancedMesh(curbGeo, curbMat, 55);
    for (let i = 0; i < 55; i++) {
      const a = b.start + ((b.end - b.start) * (i + 0.5)) / 55;
      dummy.position.set(
        Math.sin(a) * b.innerRx,
        0.15,
        Math.cos(a) * b.innerRz,
      );
      dummy.rotation.set(
        0,
        Math.atan2(b.innerRz * Math.sin(a), b.innerRx * Math.cos(a)),
        0,
      );
      dummy.scale.set(
        ((Math.hypot(b.innerRx * Math.cos(a), b.innerRz * Math.sin(a)) *
          (b.end - b.start)) /
          55 /
          0.57) *
          0.96,
        0.36,
        0.7,
      );
      dummy.updateMatrix();
      edging.setMatrixAt(i, dummy.matrix);
      edging.setColorAt(i, new THREE.Color().setScalar(0.58 + random() * 0.17));
    }
    edging.receiveShadow = true;
    scene.add(edging);
  }
  for (const b of beds) {
    const shape = new THREE.Shape();
    for (let i = 0; i <= 48; i++) {
      const a = (i / 48) * Math.PI * 2;
      const rx = b.rx * (1 + 0.08 * Math.sin(a * 3));
      const x = Math.cos(a) * rx,
        z = Math.sin(a) * b.rz;
      const wx = b.x + x * Math.cos(b.angle) - z * Math.sin(b.angle),
        wz = b.z + x * Math.sin(b.angle) + z * Math.cos(b.angle);
      if (i === 0) shape.moveTo(wx, -wz);
      else shape.lineTo(wx, -wz);
    }
    const bed = surface(new THREE.ExtrudeGeometry(shape, {depth: 0.072, bevelEnabled: false, steps: 1}), soilMat, 0.108);
    obstacles.push({ type: "ellipse", ...b });

  }
  // Fallen foliage lies only on the ground; the trees themselves are completely bare.
  const leafModel = textures.groundDetails.getObjectByName("DryLeaf");
  const fallen = new THREE.InstancedMesh(
    leafModel.geometry,
    leafModel.material,
    1640,
  );
  for (let i = 0; i < 1640; i++) {
    const a = random() * Math.PI * 2,
      r = i < 900 ? 9 + random() * 3 : 13 + random() * 9;
    dummy.position.set(
      Math.sin(a) * r,
      0.165 + random() * 0.006,
      Math.cos(a) * r * 1.17,
    );
    if (r > 12) dummy.position.y = 0.015;
    if (i >= 1400) {
      const cluster=[24.8,28.6,33.7,38.4][i%4];
      const p=streetPoint(cluster+(random()-.5)*2.1,(i%3===0?-1:1)*(3.45+random()*.37));
      dummy.position.set(p.x,.025+random()*.003,p.z);
    }
    dummy.rotation.set(0, random() * 6.28, 0);
    const leafScale = 0.45 + random();
    dummy.scale.set(leafScale * (0.65 + random() * 0.7), leafScale, leafScale);
    dummy.updateMatrix();
    fallen.setMatrixAt(i, dummy.matrix);
    fallen.setColorAt(i, new THREE.Color().setScalar(i % 3 ? 0.3 + random() * 0.25 : 0.6 + random() * 0.25));
  }
  scene.add(fallen);
  for (const [name, positions] of [
    [
      "UtilityCover",
      [
        [12, 0, 0.3],
        [-13, -5, 0.9],
        [0, 18, -0.4],
      ],
    ],
    [
      "StreetDrain",
      [
        [10.9, -2, 1.5],
        [-10.9, 1.5, 1.5],
        [1.5, 14.3, 0],
      ],
    ],
  ]) {
    for (const [x, z, a] of positions) {
      const detail = textures.groundDetails.getObjectByName(name).clone();
      detail.position.set(x, 0.009, z);
      detail.rotation.y = a;
      detail.receiveShadow = true;
      scene.add(detail);
    }
  }
  // A broad park floor recedes through bare trees beyond the graffiti wall.
  const parkMat = new THREE.MeshStandardMaterial({
    color: 0x1e2b20,
    map: noise,
    bumpMap: noise,
    bumpScale: 0.17,
    roughness: 0.98,
  });
  const park = new THREE.Mesh(new THREE.PlaneGeometry(75, 150), parkMat);
  park.rotation.x = -Math.PI / 2;
  park.position.set(61, 0.025, 0);
  park.receiveShadow = true;
  scene.add(park);
  const parkPath = new THREE.Mesh(
    new THREE.PlaneGeometry(55, 3),
    new THREE.MeshStandardMaterial({
      color: 0x515747,
      map: stoneMap,
      roughness: 0.92,
    }),
  );
  parkPath.rotation.x = -Math.PI / 2;
  parkPath.position.set(51, 0.04, -6);
  parkPath.receiveShadow = true;
  scene.add(parkPath);
  return {
    noise,
    groundMat,
    islandMat,
    pavement,
    lightMap,
    reflectionSurfaces,
    roadBase: road,
    addGroundShader,
  };
}
export function makeLamp(scene, x, z, h, kind = "street") {
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  scene.add(group);
  const iron = new THREE.MeshStandardMaterial({
    color: 0x1c2825,
    metalness: 0.72,
    roughness: 0.42,
  });
  const brass = new THREE.MeshStandardMaterial({
    color: 0x625641,
    metalness: 0.75,
    roughness: 0.36,
  });
  const glow = new THREE.MeshBasicMaterial({
    color: 0xffd396,
    toneMapped: false,
  });
  function cyl(r1, r2, hh, y, mat) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, hh, 8), mat);
    m.position.y = y;
    m.castShadow = true;
    group.add(m);
    return m;
  }
  if (kind === "column") {
    cyl(0.4, 0.43, 0.2, 0.22, iron);
    const frame = new THREE.Mesh(
      new THREE.BoxGeometry(0.35, h - 0.5, 0.35),
      iron,
    );
    frame.position.y = h / 2;
    frame.castShadow = true;
    group.add(frame);
    const panel = new THREE.Mesh(
      new THREE.BoxGeometry(0.46, h - 0.75, 0.46),
      new THREE.MeshStandardMaterial({
        color: 0xf3d8a3,
        emissive: 0xffaf42,
        emissiveIntensity: 0.75,
        roughness: 0.65,
      }),
    );
    panel.position.y = h / 2;
    group.add(panel);
    for (let a = 0; a < 4; a++) {
      const p = new THREE.Mesh(
        new THREE.BoxGeometry(0.045, h - 0.4, 0.045),
        brass,
      );
      p.position.set(
        Math.sin(Math.PI / 4 + (a * Math.PI) / 2) * 0.345,
        h / 2,
        Math.cos(Math.PI / 4 + (a * Math.PI) / 2) * 0.345,
      );
      group.add(p);
    }
    cyl(0.4, 0.38, 0.14, h - 0.18, iron);
    obstacles.push({ type: "circle", x, z, r: 0.52 });
  } else {
    cyl(0.18, 0.25, 0.25, 0.125, iron);
    cyl(0.06, 0.11, h - 0.4, h / 2, iron);
    cyl(0.34, 0.1, 0.2, h - 0.1, iron);
    cyl(
      0.25,
      0.2,
      0.5,
      h + 0.17,
      new THREE.MeshStandardMaterial({
        color: 0xffedc9,
        emissive: 0xffbb63,
        emissiveIntensity: 2,
        toneMapped: false,
      }),
    );
    cyl(0.04, 0.38, 0.24, h + 0.54, iron);
    for (let a = 0; a < 4; a++) {
      const bar = new THREE.Mesh(
        new THREE.CylinderGeometry(0.022, 0.022, 0.53, 5),
        iron,
      );
      bar.position.set(
        Math.sin((a * Math.PI) / 2) * 0.24,
        h + 0.17,
        Math.cos((a * Math.PI) / 2) * 0.24,
      );
      group.add(bar);
    }
    obstacles.push({ type: "circle", x, z, r: 0.3 });
  }
  // Merge each lantern's static ironwork: its small bars retain real geometry
  // while drawing once per material in the main view and wet reflection.
  const byMaterial = new Map();
  for (const child of [...group.children]) {
    if (!child.isMesh) continue;
    child.updateMatrix();
    if (!byMaterial.has(child.material)) byMaterial.set(child.material, []);
    byMaterial.get(child.material).push(child.geometry.clone().applyMatrix4(child.matrix));
    group.remove(child);
    child.geometry.dispose();
  }
  for (const [material, parts] of byMaterial) {
    const combined = new THREE.Mesh(mergeGeometries(parts), material);
    combined.castShadow = combined.receiveShadow = true;
    group.add(combined);
    parts.forEach((g) => g.dispose());
  }
  const glowMap = canvasTexture(64, 64, (ctx, w, h) => {
    const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, "rgba(255,205,125,.9)");
    g.addColorStop(0.08, "rgba(255,172,62,.55)");
    g.addColorStop(0.35, "rgba(255,144,30,.16)");
    g.addColorStop(1, "rgba(255,135,30,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  });
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: glowMap,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      opacity: .18,
      toneMapped: false,
    }),
  );
  sprite.position.set(0, kind === "column" ? h * 0.75 : h + 0.18, 0);
  sprite.scale.setScalar(kind === "column" ? 1.5 : 1.6);
  group.add(sprite);
  return group;
}
