import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const CYBERNET_WARRIOR_MODEL_URL = '/assest/futuristic_cybernet_warrior_high_detail_sci_fi/scene.gltf';

/**
 * Creates a soft radial alpha canvas texture for silky, glowing stardust particles.
 */
function createStardustTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 64;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255,255,255,1.0)');
  gradient.addColorStop(0.25, 'rgba(160,240,255,0.85)');
  gradient.addColorStop(0.6, 'rgba(120,80,255,0.25)');
  gradient.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

/**
 * Helper to normalize and center GLTF 3D models cleanly in the viewport.
 */
function fitModel(model, targetSize, anchorToBottom = false) {
  const bounds = new THREE.Box3().setFromObject(model);
  const size = bounds.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 0.001);
  model.scale.setScalar(targetSize / maxDim);
  const scaledBounds = new THREE.Box3().setFromObject(model);
  const center = scaledBounds.getCenter(new THREE.Vector3());
  model.position.x -= center.x;
  model.position.z -= center.z;
  model.position.y -= anchorToBottom ? scaledBounds.min.y : center.y;
}

/**
 * Creates 12,000 Fine Stardust Particle Galaxy Streams around the Cybernet Warrior.
 */
function createCosmicStardustStream(count = 12000, texture) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const basePositions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  const colorPrimary = new THREE.Color(0x00f3ff);
  const colorSecondary = new THREE.Color(0xff00a0);
  const colorTertiary = new THREE.Color(0xaa00ff);

  const innerR = 1.6;
  const outerR = 11.5;

  for (let i = 0; i < count; i++) {
    const idx3 = i * 3;
    const arms = 3;
    const armAngle = (i % arms) * ((Math.PI * 2) / arms);
    const radius = innerR + Math.pow(Math.random(), 1.4) * (outerR - innerR);
    const spinAngle = radius * 0.28;
    const angle = armAngle + spinAngle + (Math.random() - 0.5) * 0.32;

    const x = Math.cos(angle) * radius;
    const y = (Math.random() - 0.5) * (radius * 0.32) + 0.8;
    const z = Math.sin(angle) * radius;

    positions[idx3] = basePositions[idx3] = x;
    positions[idx3 + 1] = basePositions[idx3 + 1] = y;
    positions[idx3 + 2] = basePositions[idx3 + 2] = z;

    const normR = (radius - innerR) / (outerR - innerR);
    let pColor;
    if (normR < 0.5) pColor = colorPrimary.clone().lerp(colorSecondary, normR * 2.0);
    else pColor = colorSecondary.clone().lerp(colorTertiary, (normR - 0.5) * 2.0);

    colors[idx3] = pColor.r;
    colors[idx3 + 1] = pColor.g;
    colors[idx3 + 2] = pColor.b;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.13,
    map: texture,
    vertexColors: true,
    transparent: true,
    opacity: 0.68,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  const points = new THREE.Points(geometry, material);
  return { points, basePositions, material };
}

/**
 * Creates 3D Cybernet Warrior Hero Asset + Studio Lighting Setup.
 */
function createCybernetWarriorHero() {
  const root = new THREE.Group();
  root.name = 'cybernetWarriorHero';
  root.position.set(0, 0.4, 0);

  // High-intensity studio lights for metallic PBR reflections
  const ambient = new THREE.HemisphereLight(0x00f3ff, 0x17102d, 3.8);
  const keyLight = new THREE.PointLight(0x00f3ff, 14.0, 32, 2);
  keyLight.position.set(-4.0, 6.0, 5.0);

  const rimLight = new THREE.PointLight(0xff00a0, 10.0, 28, 2);
  rimLight.position.set(5.0, 4.0, -3.0);

  const fillLight = new THREE.PointLight(0x00ffaa, 6.0, 20, 2);
  fillLight.position.set(0.0, -3.0, 4.0);

  root.add(ambient, keyLight, rimLight, fillLight);

  // Soft spherical energy atmosphere glow aura behind warrior
  const auraGeo = new THREE.SphereGeometry(2.4, 32, 32);
  const auraMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    transparent: true,
    opacity: 0.18,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide
  });
  const auraMesh = new THREE.Mesh(auraGeo, auraMat);
  auraMesh.position.set(0, 0.8, 0);
  root.add(auraMesh);

  // Load the 3D Cybernet Warrior GLTF Model
  const loader = new GLTFLoader();
  loader.load(CYBERNET_WARRIOR_MODEL_URL, (gltf) => {
    const warrior = gltf.scene;
    fitModel(warrior, 4.6, false);
    warrior.position.set(0, 0.2, 0);

    warrior.traverse((object) => {
      if (!object.isMesh) return;
      object.castShadow = false;
      if (object.material) {
        object.material.side = THREE.DoubleSide;
        object.material.roughness = 0.20;
        object.material.metalness = 0.85;
        object.material.envMapIntensity = 2.5;
        object.material.needsUpdate = true;
      }
    });

    root.add(warrior);
    root.userData.warrior = warrior;
    root.userData.loaded = true;
  }, undefined, (error) => {
    console.warn('Cybernet Warrior GLTF model asset could not load:', error);
  });

  return { root, ambient, keyLight, rimLight, fillLight, auraMesh, auraMat };
}

/**
 * Creates the High-End Afterlife Cybernet Warrior 3D Visualizer Group.
 */
export function createLuxuryAbstractCinematic() {
  const group = new THREE.Group();
  group.name = 'mode_luxuryAbstractCinematic';
  group.position.y = 0.2;

  const texture = createStardustTexture();
  const heroWorld = createCybernetWarriorHero();
  group.add(heroWorld.root);

  const stardust = createCosmicStardustStream(12000, texture);
  group.add(stardust.points);

  group.userData = {
    heroWorld,
    stardust,
    emotion: 'CALM'
  };

  setLuxuryAbstractCinematicEmotion(group, 'CALM');
  return group;
}

/**
 * Updates Cybernet Warrior weightless floating motion, particle orbit, and audio reactivity.
 */
export function updateLuxuryAbstractCinematic(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group || !group.userData) return;

  const { heroWorld, stardust, emotion } = group.userData;

  let bass = beatPulse;
  let mid = 0.0;
  if (frequencyData && frequencyData.length > 0) {
    let bSum = 0, mSum = 0;
    const len = frequencyData.length;
    for (let i = 0; i < Math.floor(len * 0.2); i++) bSum += frequencyData[i];
    for (let i = Math.floor(len * 0.2); i < Math.floor(len * 0.6); i++) mSum += frequencyData[i];
    bass = Math.max(beatPulse, bSum / (len * 0.2 * 255.0));
    mid = mSum / (len * 0.4 * 255.0);
  }

  // 1. Cybernet Warrior Weightless Floating Animation & Light Pulses
  if (heroWorld && heroWorld.root) {
    heroWorld.root.position.y = 0.2 + Math.sin(elapsedTime * 0.65) * (0.12 + bass * 0.15);
    heroWorld.root.rotation.y = Math.sin(elapsedTime * 0.12) * 0.08;

    if (heroWorld.warrior) {
      heroWorld.warrior.rotation.y = elapsedTime * 0.15;
    }

    if (heroWorld.auraMesh) {
      const auraScale = 1.0 + (bass * 0.25);
      heroWorld.auraMesh.scale.set(auraScale, auraScale, auraScale);
    }

    heroWorld.keyLight.intensity = 14.0 + (bass * 8.0);
    heroWorld.rimLight.intensity = 10.0 + (bass * 6.0);
  }

  // 2. Rotate Stardust Galaxy Stream
  if (stardust && stardust.points) {
    stardust.points.rotation.y += (0.025 + bass * 0.08) * deltaTime;
    stardust.points.rotation.z = Math.sin(elapsedTime * 0.18) * 0.05;
  }
}

/**
 * Updates Cybernet Warrior lighting & aura color profiles based on active emotion state.
 */
export function setLuxuryAbstractCinematicEmotion(group, emotion = 'CALM') {
  if (!group || !group.userData) return;
  const key = String(emotion).toUpperCase();
  group.userData.emotion = key;

  const { heroWorld, stardust } = group.userData;

  const profiles = {
    CALM: { primary: 0x00f3ff, secondary: 0x8800ff, lightKey: 0x00f3ff, lightRim: 0x8800ff },
    HAPPY: { primary: 0xffaa00, secondary: 0x00f3ff, lightKey: 0xffaa00, lightRim: 0x00f3ff },
    SAD: { primary: 0x0077ff, secondary: 0x4400aa, lightKey: 0x0055ff, lightRim: 0x330088 },
    ENERGETIC: { primary: 0xff00a0, secondary: 0x00f3ff, lightKey: 0xff00a0, lightRim: 0x00f3ff }
  };

  const p = profiles[key] || profiles.CALM;

  if (heroWorld) {
    heroWorld.keyLight.color.set(p.lightKey);
    heroWorld.rimLight.color.set(p.lightRim);
    heroWorld.ambient.color.set(p.primary);
    if (heroWorld.auraMat) {
      heroWorld.auraMat.color.set(p.primary);
    }
  }

  if (stardust && stardust.material) {
    stardust.material.color.set(p.primary);
  }
}

export function armLuxuryAbstractCinematicIntro(group) {
  if (!group || !group.userData) return;
  group.userData.introActive = false;
  group.userData.introStart = null;
}

export function startLuxuryAbstractCinematicIntro(group, storyTime = 0) {
  if (!group || !group.userData) return;
  group.userData.introStart = storyTime;
  group.userData.introActive = true;
}
