import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const ROSE_MODEL_URL = '/assest/rose/scene.gltf';
const GARDEN_MODEL_URL = '/assest/leaves_in_the_garden.glb';
const BUTTERFLY_MODEL_URL = '/assest/butterfly/scene.gltf';
const RAIN_VIDEO_FILE = 'Rain_streaks_falling_black_backg…_20261008225533.mp4';
const RAIN_VIDEO_URL = `/assest/${encodeURIComponent(RAIN_VIDEO_FILE)}`;


function lineFromCurve(points, color, opacity = 0.8) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false });
  return new THREE.Line(geometry, material);
}

function branchCurve(side, height, reach, bend) {
  return new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -2.7, 0),
    new THREE.Vector3(side * 0.12, -0.7, 0.05),
    new THREE.Vector3(side * bend, height - 1.2, 0.1),
    new THREE.Vector3(side * reach, height, 0)
  ]).getPoints(48);
}

function ringPoints(radius, segments = 96) {
  const points = [];
  for (let index = 0; index < segments; index++) {
    const angle = (index / segments) * Math.PI * 2;
    points.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, 0));
  }
  return points;
}

function createCurledPetalGeometry(width, length, curl) {
  const across = 12;
  const along = 16;
  const vertices = [];
  const indices = [];
  for (let row = 0; row <= along; row++) {
    const v = row / along;
    for (let column = 0; column <= across; column++) {
      const u = column / across * 2 - 1;
      // Narrow base + broad, rounded tip. The z curve creates the rose cup.
      const x = u * width * (.18 + .82 * v);
      const y = v * length * (1 - .18 * u * u * v);
      const z = Math.sin(v * Math.PI) * curl * (1 - .55 * u * u) + u * u * .06;
      vertices.push(x, y, z);
    }
  }
  for (let row = 0; row < along; row++) {
    for (let column = 0; column < across; column++) {
      const a = row * (across + 1) + column;
      const b = a + 1;
      const c = a + across + 1;
      const d = c + 1;
      indices.push(a, c, b, b, c, d);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function createPetal(primary, secondary, index, count = 10, inner = false) {
  // Unlit colour avoids low-light grey, but normal alpha blending prevents
  // twenty overlapping rose petals from clipping to a white silhouette.
  const material = new THREE.MeshBasicMaterial({
    color: index % 2 ? secondary : primary,
    transparent: true,
    opacity: .54,
    side: THREE.DoubleSide,
    depthWrite: false
  });
  const petal = new THREE.Mesh(createCurledPetalGeometry(inner ? .50 : .78, inner ? .84 : 1.22, inner ? .15 : .34), material);
  petal.rotation.z = (index / count) * Math.PI * 2 + (inner ? Math.PI / count : 0);
  petal.rotation.x = index % 2 ? -.18 : .16;
  petal.position.z = inner ? .20 : -.10;
  const vein = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, .04, .10), new THREE.Vector3(0, inner ? .66 : 1.0, inner ? .16 : .31)]),
    new THREE.LineBasicMaterial({ color: secondary, transparent: true, opacity: .32, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  petal.add(vein);
  return petal;
}

function createPollenTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 64;
  const context = canvas.getContext('2d');
  const gradient = context.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(.22, 'rgba(220,255,255,.92)');
  gradient.addColorStop(.62, 'rgba(110,240,255,.28)');
  gradient.addColorStop(1, 'rgba(110,240,255,0)');
  context.fillStyle = gradient;
  context.fillRect(0, 0, 64, 64);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createAtmosphereTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 256;
  const context = canvas.getContext('2d');
  const gradient = context.createRadialGradient(128, 128, 0, 128, 128, 128);
  gradient.addColorStop(0, 'rgba(86, 44, 185, .42)');
  gradient.addColorStop(.38, 'rgba(20, 92, 185, .18)');
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
  context.fillStyle = gradient;
  context.fillRect(0, 0, 256, 256);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createCosmicAtmosphere() {
  const group = new THREE.Group();
  group.name = 'cosmicBloomAtmosphere';
  const fogTexture = createAtmosphereTexture();
  const fogs = [
    { x: -4.4, y: 1.6, z: -4.8, scale: 10.4, color: 0x264cb7, opacity: .50 },
    { x: 4.1, y: -.4, z: -4.7, scale: 9.5, color: 0x9b239b, opacity: .46 },
    { x: 0, y: -3.2, z: -4.9, scale: 14.5, color: 0x164fa6, opacity: .38 },
    { x: .5, y: 2.8, z: -5.1, scale: 8.2, color: 0x5c2aad, opacity: .34 }
  ].map(config => {
    const material = new THREE.SpriteMaterial({ map: fogTexture, color: config.color, transparent: true, opacity: config.opacity, blending: THREE.AdditiveBlending, depthWrite: false });
    const sprite = new THREE.Sprite(material);
    sprite.position.set(config.x, config.y, config.z);
    sprite.scale.setScalar(config.scale);
    group.add(sprite);
    return sprite;
  });
  const starCount = 230;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(starCount * 3);
  for (let index = 0; index < starCount; index++) {
    positions[index * 3] = (Math.random() - .5) * 17;
    positions[index * 3 + 1] = (Math.random() - .5) * 10;
    positions[index * 3 + 2] = -4.3 - Math.random() * 2;
  }
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const stars = new THREE.Points(geometry, new THREE.PointsMaterial({ map: createPollenTexture(), color: 0x8ca8ff, size: .09, transparent: true, opacity: .5, blending: THREE.AdditiveBlending, depthWrite: false }));
  group.add(stars);
  return { group, fogs, stars };
}

function createGardenEnvironment() {
  const group = new THREE.Group();
  group.name = 'neonRoseGarden';
  const pollenTexture = createPollenTexture();
  const ground = new THREE.Mesh(
    // A wide field has no visible circular edge.  The old disc read as a
    // dark planet beneath the flower instead of a garden floor.
    new THREE.PlaneGeometry(22, 13, 1, 1),
    new THREE.MeshBasicMaterial({ color: 0x0a2a1b, transparent: true, opacity: 0.58, depthWrite: false, side: THREE.DoubleSide })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(0, -4.13, -3.1);
  ground.visible = false;
  group.add(ground);

  // This becomes a moon, warm sun, or storm glow depending on the emotion.
  const skyGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: pollenTexture, color: 0x7bbcff, transparent: true, opacity: 0.34, blending: THREE.AdditiveBlending, depthWrite: false }));
  skyGlow.position.set(-3.9, 3.1, -3.5);
  skyGlow.scale.set(5.5, 5.5, 1);
  skyGlow.visible = false;
  group.add(skyGlow);

  const grassGroup = new THREE.Group();
  const grassMaterial = new THREE.LineBasicMaterial({ color: 0x2c7846, transparent: true, opacity: 0.56, depthWrite: false });
  for (let index = 0; index < 360; index++) {
    const x = (Math.random() - .5) * 12.6;
    const baseY = -3.98 + (Math.random() - .5) * .18;
    const height = .08 + Math.random() * .38;
    const lean = (Math.random() - .5) * .16;
    const blade = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, baseY, -1.8),
      new THREE.Vector3(x + lean, baseY + height, -1.8)
    ]), grassMaterial);
    grassGroup.add(blade);
  }
  group.add(grassGroup);
  grassGroup.visible = false;

  const fireflyCount = 76;
  const fireflyGeometry = new THREE.BufferGeometry();
  const fireflyPositions = new Float32Array(fireflyCount * 3);
  const fireflyBase = new Float32Array(fireflyCount * 3);
  for (let index = 0; index < fireflyCount; index++) {
    const x = (Math.random() - .5) * 10.5;
    const y = -3.35 + Math.random() * 4.9;
    const z = -1.4 - Math.random() * 1.5;
    fireflyPositions.set([x, y, z], index * 3);
    fireflyBase.set([x, y, z], index * 3);
  }
  fireflyGeometry.setAttribute('position', new THREE.BufferAttribute(fireflyPositions, 3));
  const fireflies = new THREE.Points(fireflyGeometry, new THREE.PointsMaterial({ map: pollenTexture, color: 0xffdc77, size: .13, transparent: true, opacity: .72, blending: THREE.AdditiveBlending, depthWrite: false }));
  group.add(fireflies);

  const rainCount = 150;
  const rainGeometry = new THREE.BufferGeometry();
  const rainPositions = new Float32Array(rainCount * 6);
  const rainVelocity = new Float32Array(rainCount);
  const rainDrift = new Float32Array(rainCount);
  for (let index = 0; index < rainCount; index++) {
    const x = (Math.random() - .5) * 12;
    const y = -3.5 + Math.random() * 8;
    const z = -1.2 - Math.random() * 1.5;
    rainVelocity[index] = 2.5 + Math.random() * 3.4;
    rainDrift[index] = -.24 + Math.random() * .48;
    rainPositions.set([x, y, z, x - rainDrift[index] * .20, y - (.16 + rainVelocity[index] * .045), z], index * 6);
  }
  rainGeometry.setAttribute('position', new THREE.BufferAttribute(rainPositions, 3));
  const rain = new THREE.LineSegments(rainGeometry, new THREE.LineBasicMaterial({ color: 0x78bcff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  group.add(rain);

  return { group, ground, skyGlow, grassGroup, fireflies, fireflyBase, rain, rainVelocity, rainDrift };
}

function createGardenAsset() {
  const root = new THREE.Group();
  root.name = 'realisticGardenAsset';
  root.visible = false;

  const sunlight = new THREE.DirectionalLight(0xffd7a3, 3.0);
  sunlight.position.set(-4, 8, 3);
  root.add(sunlight);
  const skyFill = new THREE.HemisphereLight(0x9bd6ff, 0x183b22, 1.35);
  root.add(skyFill);

  new GLTFLoader().load(GARDEN_MODEL_URL, (gltf) => {
    const model = gltf.scene;
    const bounds = new THREE.Box3().setFromObject(model);
    const size = bounds.getSize(new THREE.Vector3());
    // Fit any authoring scale into our 18-unit cinematic stage.  A garden
    // asset is scenery: wide enough to fill the frame, never larger than it.
    const horizontalSize = Math.max(size.x, size.z, .001);
    const scale = 19 / horizontalSize;
    model.scale.setScalar(scale);
    const scaledBounds = new THREE.Box3().setFromObject(model);
    const center = scaledBounds.getCenter(new THREE.Vector3());
    model.position.x -= center.x;
    model.position.z -= center.z + 2.6;
    model.position.y -= scaledBounds.min.y + 4.12;
    model.traverse((object) => {
      if (!object.isMesh) return;
      object.castShadow = false;
      object.receiveShadow = true;
      if (object.material) {
        object.material.side = THREE.DoubleSide;
        object.material.envMapIntensity = .4;
      }
    });
    root.add(model);
    root.userData.model = model;
    root.userData.loaded = true;
    root.visible = true;
  }, undefined, (error) => console.warn('Garden asset could not load.', error));

  return { root, sunlight, skyFill };
}

function createButterflyAsset() {
  const root = new THREE.Group();
  root.name = 'happyButterflyAsset';
  root.visible = false;
  new GLTFLoader().load(BUTTERFLY_MODEL_URL, (gltf) => {
    const model = gltf.scene;
    const bounds = new THREE.Box3().setFromObject(model);
    const size = bounds.getSize(new THREE.Vector3());
    model.scale.setScalar(.42 / Math.max(size.y, .001));
    const scaledBounds = new THREE.Box3().setFromObject(model);
    const center = scaledBounds.getCenter(new THREE.Vector3());
    model.position.sub(center);
    model.traverse((object) => {
      if (object.isMesh && object.material) {
        object.material.side = THREE.DoubleSide;
        object.material.envMapIntensity = .75;
      }
    });
    root.add(model);
    root.userData.loaded = true;
    root.userData.mixer = gltf.animations.length ? new THREE.AnimationMixer(model) : null;
    gltf.animations.forEach((clip) => root.userData.mixer?.clipAction(clip).play());
    root.visible = true;
  }, undefined, (error) => console.warn('Butterfly asset could not load.', error));
  return root;
}

function createRainVideoOverlay() {
  const video = document.createElement('video');
  video.src = RAIN_VIDEO_URL;
  video.loop = true;
  video.muted = true;
  video.playsInline = true;
  video.preload = 'auto';
  const texture = new THREE.VideoTexture(video);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.MeshBasicMaterial({
    map: texture,
    transparent: true,
    opacity: 0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    depthTest: false
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(13.8, 8.1), material);
  mesh.name = 'realRainVideoOverlay';
  mesh.position.set(0, .15, 3.0);
  mesh.renderOrder = 20;
  mesh.visible = false;
  return { mesh, material, video };
}

function createRealRose() {
  const root = new THREE.Group();
  root.name = 'realisticRoseAsset';
  root.position.set(0, -4.05, 0.18);
  root.visible = false;

  // The scanned asset uses PBR materials. These lights are part of the rose
  // scene, so it keeps its realistic volume even when the rest of the visual
  // uses glow-based materials.
  const warmKey = new THREE.DirectionalLight(0xffd1b8, 2.35);
  warmKey.position.set(-3.2, 5.2, 4.8);
  root.add(warmKey);
  const coolFill = new THREE.DirectionalLight(0x83baff, 1.25);
  coolFill.position.set(3.4, 1.8, 3.1);
  root.add(coolFill);
  const rim = new THREE.PointLight(0xff3a8a, 4.5, 6.5, 2);
  rim.position.set(0, 3.05, 1.8);
  root.add(rim);

  const loader = new GLTFLoader();
  loader.load(ROSE_MODEL_URL, (gltf) => {
    const model = gltf.scene;
    // Authoring scale differs per asset. Normalising its bounding box keeps
    // the flower consistently framed in this visual family.
    const bounds = new THREE.Box3().setFromObject(model);
    const size = bounds.getSize(new THREE.Vector3());
    const scale = 4.25 / Math.max(size.y, .001);
    model.scale.setScalar(scale);
    const scaledBounds = new THREE.Box3().setFromObject(model);
    const center = scaledBounds.getCenter(new THREE.Vector3());
    model.position.x -= center.x;
    model.position.z -= center.z;
    model.position.y -= scaledBounds.min.y;
    model.traverse((object) => {
      if (!object.isMesh) return;
      object.castShadow = true;
      object.receiveShadow = true;
      if (object.material) {
        object.material.side = THREE.DoubleSide;
        object.material.envMapIntensity = .65;
      }
    });
    root.add(model);
    root.userData.model = model;
    root.userData.loaded = true;
    root.visible = true;
  }, undefined, (error) => {
    // Leave the atmosphere running if a user removes the optional asset.
    console.warn('Real rose asset could not load.', error);
  });
  return { root, warmKey, coolFill, rim };
}

/**
 * A procedural luminous tree/bloom inspired by sacred-geometry artwork.
 * It uses only generated lines, points, and orbit circles, so it remains
 * lightweight and fully beat-reactive.
 */
export function createCosmicBloom() {
  const group = new THREE.Group();
  group.name = 'mode_cosmicBloom';
  group.position.y = 1.4;

  const primary = new THREE.Color(0x33f7e7);
  const secondary = new THREE.Color(0xac6bff);
  // The object identity is deliberately stable: this is a rose in every song.
  // Emotion controls the atmosphere, pollen and energy, not whether the rose
  // suddenly turns grey/blue and becomes unrecognisable.
  const rosePrimary = new THREE.Color(0xd91445);
  const roseSecondary = new THREE.Color(0xff5a80);
  const roseVein = new THREE.Color(0xffb1c0);
  const atmosphere = createCosmicAtmosphere();
  const garden = createGardenEnvironment();
  const gardenAsset = createGardenAsset();
  const realRose = createRealRose();
  const butterfly = createButterflyAsset();
  const rainVideo = createRainVideoOverlay();
  group.add(garden.group);
  group.add(atmosphere.group);
  group.add(gardenAsset.root);
  group.add(realRose.root);
  realRose.root.add(butterfly);
  group.add(rainVideo.mesh);
  const branches = [];
  const configs = [
    { height: 2.9, reach: 2.7, bend: 0.82 },
    { height: 2.2, reach: 3.45, bend: 1.45 },
    { height: 1.45, reach: 3.85, bend: 1.90 },
    { height: 0.70, reach: 3.35, bend: 1.65 }
  ];
  configs.forEach((config, branchIndex) => {
    [-1, 1].forEach(side => {
      const branch = lineFromCurve(branchCurve(side, config.height, config.reach, config.bend), branchIndex % 2 === 0 ? primary : secondary, 0.82);
      group.add(branch);
      branches.push({ line: branch, material: branch.material, side, branchIndex });
    });
  });

  const trunk = lineFromCurve(new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -3.1, 0), new THREE.Vector3(-0.12, -1.1, 0), new THREE.Vector3(0.16, 0.65, 0), new THREE.Vector3(0, 3.55, 0)
  ]).getPoints(68), primary, 0.92);
  group.add(trunk);

  const orbits = [];
  [1.3, 2.45, 3.65].forEach((radius, index) => {
    const orbit = lineFromCurve(ringPoints(radius), index % 2 ? secondary : primary, 0.44);
    orbit.rotation.x = index === 0 ? 0.36 : -0.18;
    // These rings are kept for a brief drop accent only; leaving them visible
    // all the time made the flower read as a technical diagram.
    orbit.visible = false;
    group.add(orbit);
    orbits.push({ line: orbit, material: orbit.material, speed: (index % 2 ? -1 : 1) * (0.12 + index * 0.05) });
  });

  const leafCount = 880;
  const positions = new Float32Array(leafCount * 3);
  const basePositions = new Float32Array(leafCount * 3);
  for (let index = 0; index < leafCount; index++) {
    // A controlled pollen aura supports the bloom silhouette. The earlier
    // tree-shaped cloud looked like disconnected visual noise.
    const angle = (index / leafCount) * Math.PI * 2 + (Math.random() - .5) * .38;
    const radius = .55 + Math.pow(Math.random(), .72) * 2.05;
    const x = Math.cos(angle) * radius * 1.05;
    const y = -.65 + Math.sin(angle) * radius * .76;
    const z = (Math.random() - 0.5) * 0.65;
    positions[index * 3] = basePositions[index * 3] = x;
    positions[index * 3 + 1] = basePositions[index * 3 + 1] = y;
    positions[index * 3 + 2] = basePositions[index * 3 + 2] = z;
  }
  const leafGeometry = new THREE.BufferGeometry();
  leafGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const leafMaterial = new THREE.PointsMaterial({ color: primary, map: createPollenTexture(), size: 0.095, transparent: true, opacity: 0.70, blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true });
  const leaves = new THREE.Points(leafGeometry, leafMaterial);
  group.add(leaves);

  const heart = new THREE.Mesh(new THREE.CircleGeometry(0.19, 48), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.66, blending: THREE.AdditiveBlending, depthWrite: false }));
  heart.position.y = -0.65;
  group.add(heart);

  // A recognisable flower is the narrative anchor. It begins as a seed and
  // opens only when the track gathers enough energy.
  const petalGroup = new THREE.Group();
  petalGroup.position.y = -0.65;
  // Three uneven rings create a rose cup: broad outer petals, then a tighter
  // middle ring and a curled core. It deliberately avoids a perfect mandala.
  const roseLayers = [
    { count: 8, scale: 1.05, phase: 0, z: -.18, lift: -.12, tilt: .34 },
    { count: 7, scale: .74, phase: .30, z: .04, lift: .00, tilt: .03 },
    { count: 6, scale: .48, phase: .54, z: .23, lift: .12, tilt: -.22 }
  ];
  let petalNumber = 0;
  const petals = roseLayers.flatMap((layer, layerIndex) => Array.from({ length: layer.count }, (_, localIndex) => {
    const petal = createPetal(rosePrimary, roseSecondary, localIndex, layer.count, layerIndex > 0);
    const angleJitter = [.00, .10, -.07, .06, -.12, .04, -.05, .08][localIndex % 8];
    petal.rotation.z += layer.phase + angleJitter;
    petal.position.set(0, layer.lift, layer.z);
    const finalPosition = petal.position.clone();
    const currentNumber = petalNumber++;
    petal.userData = {
      finalPosition,
      finalRotation: petal.rotation.z,
      finalTilt: layer.tilt + (localIndex % 2 ? .035 : -.025),
      arrivalDelay: 5.2 + currentNumber * 1.26,
      // Start as a compact bud. Never fly in from offscreen: that made the
      // flower read as an exploding umbrella instead of a living rose.
      startPosition: new THREE.Vector3((currentNumber % 3 - 1) * .026, layer.lift * .12, layer.z * .12),
      startRotation: (currentNumber % 5 - 2) * .045,
      budPosition: new THREE.Vector3((currentNumber % 3 - 1) * .032, layer.lift * .18, layer.z * .18),
      budRotation: (currentNumber % 5 - 2) * .09,
      layerScale: layer.scale * .64 * (1 + (localIndex % 3 - 1) * .055)
    };
    petalGroup.add(petal);
    return petal;
  }));
  group.add(petalGroup);

  // Growth phase: a stem and two leaves make the bud read as a living flower,
  // not simply a floating mandala.
  const stemCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -.62, -.08), new THREE.Vector3(-.06, -1.65, -.10),
    new THREE.Vector3(.10, -2.75, -.08), new THREE.Vector3(0, -3.95, 0)
  ]);
  const stem = new THREE.Mesh(new THREE.TubeGeometry(stemCurve, 48, .035, 8, false), new THREE.MeshBasicMaterial({ color: 0x1c8158, transparent: true, opacity: .55, blending: THREE.AdditiveBlending, depthWrite: false }));
  group.add(stem);
  const plantLeaves = [-1, 1].map((side, index) => {
    const leaf = createPetal(0x1b8a5e, 0x6fe7a7, index, 2);
    leaf.position.set(side * .05, -2.35, .02);
    leaf.rotation.z = side < 0 ? -1.26 : 1.26;
    leaf.scale.set(.72, .72, .72);
    group.add(leaf);
    return leaf;
  });

  branches.forEach(({ line }) => { line.visible = false; });
  trunk.visible = false;
  // The GLTF rose is the hero asset. Keep the previous procedural flower
  // in memory only as a non-rendered fallback while the asset is loading.
  petalGroup.visible = false;
  stem.visible = false;
  plantLeaves.forEach((leaf) => { leaf.visible = false; });
  heart.visible = false;
  heart.material.color.set(0xffc16b);
  group.userData = { branches, trunk, orbits, leaves, leafMaterial, basePositions, heart, petalGroup, petals, stem, plantLeaves, atmosphere, garden, gardenAsset, realRose, butterfly, rainVideo, primary, secondary, rosePrimary, roseSecondary, roseVein, emotionCategory: 'CALM', intro: { armed: true, startTime: 0 }, life: { lastChapter: 'DORMANT', surgeCount: 0, outroStart: -1 } };
  return group;
}

export function updateCosmicBloom(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0, chapter = { key: 'FLOW' }, storyTime = elapsedTime) {
  if (!group?.userData) return;
  const { branches, trunk, orbits, leaves, basePositions, heart, petalGroup, petals, stem, plantLeaves, atmosphere, garden, gardenAsset, realRose, butterfly, rainVideo, intro, life } = group.userData;
  const emotion = group.userData.emotionCategory || 'CALM';
  let midEnergy = 0.24;
  if (frequencyData?.length) {
    const start = Math.floor(frequencyData.length * 0.17);
    const end = Math.floor(frequencyData.length * 0.58);
    let sum = 0;
    for (let index = start; index < end; index++) sum += frequencyData[index];
    midEnergy = sum / Math.max(1, (end - start) * 255);
  }
  const key = chapter.key || 'FLOW';
  const dormant = key === 'DORMANT';
  const build = key === 'BUILD';
  const surge = key === 'SURGE';
  const release = key === 'RELEASE';
  const open = dormant ? .08 : release ? .46 : build ? .72 : surge ? 1 : .36;
  if (surge && life.lastChapter !== 'SURGE') life.surgeCount += 1;
  life.lastChapter = key;
  // The narrative follows the actual song timestamp, never an unrelated page clock.
  const introAge = intro?.armed ? Math.max(0, storyTime - intro.startTime) : 99;
  // Long-form opening tied to the song timeline:
  // 0-7 seed, 8-36 petal assembly, 36-43 closed bud, 43-60 bloom.
  const introBloom = intro?.armed ? smoothstep(43.0, 60.0, introAge) : 1;
  const introFade = intro?.armed ? smoothstep(.8, 4.2, introAge) * introBloom : 1;
  const growth = intro?.armed ? smoothstep(16.0, 39.0, introAge) : 1;
  const wilt = (release || dormant) ? smoothstep(.35, 4.8, chapter.age || 0) : 0;
  const rebirth = surge && life.surgeCount > 1 && introBloom > .95 ? smoothstep(.04, 1.5, chapter.age || 0) : 0;
  const outro = life.outroStart >= 0 ? smoothstep(.2, 5.8, storyTime - life.outroStart) : 0;

  atmosphere.fogs.forEach((fog, index) => {
    fog.material.opacity = (.13 + index * .035 + midEnergy * .12 + (surge ? .06 : 0)) * (1 - outro);
    fog.position.x += Math.sin(elapsedTime * (.05 + index * .01) + index) * deltaTime * .18;
  });
  atmosphere.stars.rotation.z += deltaTime * .006;

  // Garden environment: moonlight gives calm scenes a home, while release
  // brings rain and a dimmer garden without changing the Rose family itself.
  const mood = {
    CALM: { fog: 0.72, fireflies: 0.22, rain: 0, halo: 0.52, sway: 0.65, sky: 0x77baff, stars: .64, ground: 0x0a2a1b },
    HAPPY: { fog: 1.10, fireflies: 0, rain: 0, halo: 0.72, sway: 1.00, sky: 0xffc35f, stars: .03, ground: 0x236837 },
    SAD: { fog: 0.42, fireflies: 0, rain: 1, halo: 0.18, sway: 0.42, sky: 0x7899c7, stars: .06, ground: 0x10293a },
    ENERGETIC: { fog: 1.05, fireflies: 0.34, rain: 0, halo: 0.82, sway: 1.42, sky: 0xff5ba6, stars: .82, ground: 0x162052 }
  }[emotion] || { fog: .72, fireflies: .42, rain: 0, halo: .52, sway: .65, sky: 0x77baff, stars: .64, ground: 0x0a2a1b };
  const gardenEnergy = .20 + midEnergy * .40 + (surge ? .18 : 0);
  atmosphere.stars.material.opacity = (.16 + highEnergy(frequencyData) * .25 + (surge ? .10 : 0)) * mood.stars * (1 - outro);
  garden.ground.visible = false;
  garden.grassGroup.visible = false;
  garden.skyGlow.visible = false;
  garden.grassGroup.children.forEach((blade, index) => {
    blade.rotation.z = Math.sin(elapsedTime * (.48 + (index % 4) * .08) + index) * (.03 + midEnergy * .09) * mood.sway;
  });
  const fireflyPositions = garden.fireflies.geometry.attributes.position.array;
  for (let index = 0; index < garden.fireflies.geometry.attributes.position.count; index++) {
    const phase = elapsedTime * (.50 + (index % 5) * .07) + index * 1.71;
    fireflyPositions[index * 3] = garden.fireflyBase[index * 3] + Math.sin(phase) * (.08 + midEnergy * .18);
    fireflyPositions[index * 3 + 1] = garden.fireflyBase[index * 3 + 1] + Math.cos(phase * .77) * (.08 + midEnergy * .12);
  }
  garden.fireflies.geometry.attributes.position.needsUpdate = true;
  garden.fireflies.material.opacity = (.16 + (release ? .04 : .38) + highEnergy(frequencyData) * .22) * mood.fireflies * (1 - outro);
  garden.rain.visible = mood.rain > 0 || release;
  garden.rain.material.opacity = ((mood.rain ? .06 + midEnergy * .10 : release ? .05 + midEnergy * .08 : 0)) * (1 - outro);
  if (garden.rain.visible) {
    const rainPositions = garden.rain.geometry.attributes.position.array;
    for (let index = 0; index < garden.rainVelocity.length; index++) {
      const offset = index * 6;
      const fallSpeed = garden.rainVelocity[index] * (1 + midEnergy * .30);
      const wind = garden.rainDrift[index] + Math.sin(elapsedTime * .45) * .035 + beatPulse * .11;
      rainPositions[offset] += wind * deltaTime;
      rainPositions[offset + 1] -= fallSpeed * deltaTime;
      rainPositions[offset + 3] = rainPositions[offset] - wind * .22;
      rainPositions[offset + 4] = rainPositions[offset + 1] - (.16 + fallSpeed * .045);
      if (rainPositions[offset + 1] < -4.12 || Math.abs(rainPositions[offset]) > 7.2) {
        const resetY = 3.8 + Math.random() * 2.8;
        const resetX = (Math.random() - .5) * 12;
        rainPositions[offset] = resetX;
        rainPositions[offset + 1] = resetY;
        rainPositions[offset + 3] = resetX - garden.rainDrift[index] * .22;
        rainPositions[offset + 4] = resetY - (.16 + garden.rainVelocity[index] * .045);
      }
    }
    garden.rain.geometry.attributes.position.needsUpdate = true;
  }

  if (gardenAsset?.root?.userData?.loaded) {
    gardenAsset.root.visible = outro < .99;
    gardenAsset.sunlight.color.set(emotion === 'HAPPY' ? 0xffdc9c : emotion === 'SAD' ? 0x7c9cc9 : mood.sky);
    gardenAsset.sunlight.intensity = 1.75 + mood.halo * 1.5 + (surge ? .45 : 0);
    gardenAsset.skyFill.intensity = emotion === 'SAD' ? .70 : .95 + mood.halo * .34;
    gardenAsset.root.rotation.y = Math.sin(elapsedTime * .035) * .018;
  }

  const showVideoRain = emotion === 'SAD' && outro < .98;
  rainVideo.mesh.visible = showVideoRain;
  rainVideo.material.opacity = showVideoRain ? .50 + midEnergy * .18 : 0;
  if (showVideoRain && rainVideo.video.paused) {
    rainVideo.video.play().catch(() => {});
  }

  stem.visible = false;
  stem.scale.y = growth * (1 - outro);
  stem.material.opacity = (.16 + growth * .42) * (1 - outro);
  plantLeaves.forEach((leaf, index) => {
    leaf.visible = false;
    const leafLife = Math.max(0, growth - wilt * .35) * (1 - outro);
    leaf.scale.setScalar(.70 * leafLife);
    leaf.material.opacity = .18 + leafLife * .26;
    leaf.rotation.z = (index ? 1 : -1) * (1.20 + wilt * .26 + Math.sin(elapsedTime * .8 + index) * .05);
  });

  // Petals and dust carry the story. The previous branch network distracted
  // from the recognisable flower silhouette, so it intentionally stays hidden.
  orbits.forEach(({ line, speed }, index) => {
    // Rose uses pollen and halo for peaks; orbit diagrams make it look technical.
    line.visible = false;
    line.rotation.z += speed * deltaTime * (1 + midEnergy);
    line.scale.setScalar(.50 + open * .20 + beatPulse * .06);
    line.material.opacity = .06 + highEnergy(frequencyData) * .10 + (surge ? .10 : 0);
  });
  const position = leaves.geometry.attributes.position.array;
  for (let index = 0; index < leaves.geometry.attributes.position.count; index++) {
    const phase = elapsedTime * 0.9 + index * 0.17;
    const burstScale = 1 + rebirth * 2.2;
    position[index * 3] = basePositions[index * 3] * burstScale + Math.sin(phase) * (0.025 + midEnergy * 0.09);
    position[index * 3 + 1] = -.65 + (basePositions[index * 3 + 1] + .65) * burstScale + Math.cos(phase * 0.8) * (0.025 + midEnergy * 0.08) + beatPulse * .05 - wilt * (index % 7) * .012;
  }
  leaves.geometry.attributes.position.needsUpdate = true;
  leaves.scale.setScalar((.30 + open * .24 + beatPulse * .05 + rebirth * .18) * introFade * (1 - outro));
  leafMaterialOpacity(leaves, dormant, release, surge);
  leaves.material.opacity *= introFade;
  const seedFade = intro?.armed ? smoothstep(.10, .90, introAge) : 1;
  heart.scale.setScalar((.18 + open * .34 + beatPulse * .18 + midEnergy * .06) * seedFade);
  heart.material.opacity = (.24 + open * .38 + (surge ? .18 : 0)) * seedFade * (outro > .75 ? .65 : 1);
  petalGroup.visible = false;
  petalGroup.rotation.z += deltaTime * (.08 + midEnergy * .16 + (surge ? .15 : 0));
  // The assembled bud should feel substantial before it opens.
  petalGroup.scale.setScalar((.72 + introBloom * (.10 + open * .26) + rebirth * .12) * (1 - outro * .78));
  petals.forEach((petal, index) => {
    const breath = 1 + Math.sin(elapsedTime * 1.7 + index * .7) * (.025 + midEnergy * .05);
    const layer = petal.userData.layerScale;
    const arrival = intro?.armed ? smoothstep(petal.userData.arrivalDelay, petal.userData.arrivalDelay + 5.4, introAge) : 1;
    const budPosition = new THREE.Vector3().lerpVectors(petal.userData.startPosition, petal.userData.budPosition, arrival);
    petal.position.lerpVectors(budPosition, petal.userData.finalPosition, introBloom);
    petal.position.y -= wilt * (.10 + (index % 4) * .09);
    petal.position.x += rebirth * Math.cos(index * 2.4) * .22;
    const budRotation = THREE.MathUtils.lerp(petal.userData.startRotation, petal.userData.budRotation, arrival);
    petal.rotation.z = THREE.MathUtils.lerp(budRotation, petal.userData.finalRotation, introBloom) + wilt * (index % 2 ? .16 : -.16);
    petal.rotation.x = petal.userData.finalTilt + Math.sin(elapsedTime * .8 + index) * (.035 + midEnergy * .10) + beatPulse * .07;
    const budScale = .72 + introBloom * (open * layer - .72);
    petal.scale.set(budScale * breath * arrival, budScale * (1 + beatPulse * .10) * arrival);
    petal.material.opacity = (.20 + introBloom * (.40 + open * .18 + (surge ? .08 : 0))) * arrival * (1 - outro);
  });

  if (realRose?.root?.userData?.loaded) {
    // A real rose cannot be assembled petal by petal without an animated
    // asset.  This deliberately slow grounded growth is the believable
    // visual substitute: garden first, stem/rose then emerge over ~40 sec.
    const roseLife = Math.max(.01, (intro?.armed ? smoothstep(8.0, 46.0, introAge) : 1) * (1 - outro));
    const pulse = 1 + beatPulse * .055 + midEnergy * .028 + (surge ? .025 : 0);
    realRose.root.visible = outro < .99;
    realRose.root.scale.setScalar(roseLife * pulse);
    realRose.root.rotation.y += deltaTime * (.045 + midEnergy * .035);
    realRose.root.rotation.z = Math.sin(elapsedTime * .58) * .035 * mood.sway + beatPulse * .016;
    realRose.warmKey.intensity = 1.25 + mood.halo * .75 + midEnergy * .28;
    realRose.coolFill.intensity = emotion === 'SAD' ? .65 : 1.0 + highEnergy(frequencyData) * .45;
    realRose.rim.color.set(mood.sky);
    realRose.rim.intensity = 1.8 + mood.halo * 2.4 + beatPulse * 1.8;

    const showButterfly = emotion === 'HAPPY' && roseLife > .72 && outro < .96;
    butterfly.visible = showButterfly;
    if (showButterfly) {
      // HAPPY has a visible but gentle flight loop above the bloom. It reads
      // as a living garden moment, not a technical orbit or a static prop.
      const flight = elapsedTime * .78;
      butterfly.scale.setScalar(1.55);
      butterfly.position.set(
        Math.sin(flight) * .62,
        4.05 + Math.sin(flight * 2.0) * .18,
        .54 + Math.cos(flight) * .22
      );
      butterfly.rotation.set(.12 + Math.sin(flight * 2) * .10, Math.PI * .76 + Math.cos(flight) * .42, Math.sin(flight) * .16);
      butterfly.userData.mixer?.update(deltaTime);
    }
  }
}

function smoothstep(min, max, value) {
  const t = THREE.MathUtils.clamp((value - min) / (max - min), 0, 1);
  return t * t * (3 - 2 * t);
}

export function startCosmicBloomIntro(group, elapsedTime = 0) {
  if (!group?.userData?.intro) return;
  group.userData.intro.armed = true;
  group.userData.intro.startTime = elapsedTime;
}

export function armCosmicBloomIntro(group) {
  if (!group?.userData?.intro) return;
  group.userData.intro.armed = true;
  // The timer is replaced by actual playback time in startCosmicBloomIntro.
  group.userData.intro.startTime = Number.POSITIVE_INFINITY;
}

export function startCosmicBloomOutro(group, elapsedTime = 0) {
  if (!group?.userData?.life) return;
  group.userData.life.outroStart = elapsedTime;
}

function highEnergy(frequencyData) {
  if (!frequencyData?.length) return .12;
  const start = Math.floor(frequencyData.length * .65);
  let total = 0;
  for (let index = start; index < frequencyData.length; index++) total += frequencyData[index];
  return total / Math.max(1, (frequencyData.length - start) * 255);
}

function leafMaterialOpacity(leaves, dormant, release, surge) {
  if (!leaves?.material) return;
  // The garden GLB already supplies real foliage. Keep this generated layer
  // as a subtle audio pollen accent, never a screen-filling dot cloud.
  leaves.material.opacity = dormant ? .025 : release ? .08 : .10 + (surge ? .06 : 0);
}

export function setCosmicBloomColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { branches, trunk, orbits, leafMaterial, heart, petals = [], primary, secondary, rosePrimary, roseSecondary, roseVein } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.42, 0.04, 0.04));
  branches.forEach(({ material, branchIndex }) => material.color.copy(branchIndex % 2 ? secondary : primary));
  trunk.material.color.copy(primary);
  orbits.forEach(({ material }, index) => material.color.copy(index % 2 ? secondary : primary));
  leafMaterial.color.copy(primary);
  heart.material.color.set(0xffc16b);
  petals.forEach((petal, index) => {
    const color = index % 2 ? roseSecondary : rosePrimary;
    petal.material.color.copy(color);
    if (petal.children[0]?.material) petal.children[0].material.color.copy(roseVein);
  });
}

export function setCosmicBloomEmotion(group, emotionCategory) {
  if (!group?.userData) return;
  group.userData.emotionCategory = String(emotionCategory || 'CALM').toUpperCase();
}
