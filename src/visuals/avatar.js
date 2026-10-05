import * as THREE from 'three';

/**
 * Creates 3D Cyber Particle Humanoid Avatar & Dynamic Entity System.
 * Generates a 1,500+ node particle humanoid silhouette with glowing chest core and floor shockwaves.
 * 
 * @param {string} initialForm - 'CYBER_KINETIC_HUMANOID' | 'EUPHORIC_DANCER_AVATAR' | 'ASTRAL_HOLOGRAM_ENTITY' | 'GHOST_WIREFRAME_SPIRIT'
 * @param {number|string|THREE.Color} initialColor - Hex color (default: 0x00f3ff)
 * @returns {THREE.Group} Group containing 3D Avatar Entity
 */
export function create3DAvatarEntity(initialForm = 'CYBER_KINETIC_HUMANOID', initialColor = 0x00f3ff) {
  const avatarGroup = new THREE.Group();
  avatarGroup.name = '3dAvatarEntity';

  // 1. Build Humanoid Body Particle Nodes (Head, Spine, Chest, Arms, Legs)
  const nodeCount = 1600;
  const positions = new Float32Array(nodeCount * 3);
  const basePositions = new Float32Array(nodeCount * 3);
  const colors = new Float32Array(nodeCount * 3);

  const baseColorObj = new THREE.Color(initialColor);

  let particleIdx = 0;

  // Helper to generate particle cluster points for body parts
  const addCluster = (cx, cy, cz, rx, ry, rz, count) => {
    for (let i = 0; i < count && particleIdx < nodeCount; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);

      const dx = rx * Math.sin(phi) * Math.cos(theta);
      const dy = ry * Math.sin(phi) * Math.sin(theta);
      const dz = rz * Math.cos(phi);

      const px = cx + dx;
      const py = cy + dy;
      const pz = cz + dz;

      const idx3 = particleIdx * 3;
      positions[idx3] = px;
      positions[idx3 + 1] = py;
      positions[idx3 + 2] = pz;

      basePositions[idx3] = px;
      basePositions[idx3 + 1] = py;
      basePositions[idx3 + 2] = pz;

      colors[idx3] = baseColorObj.r;
      colors[idx3 + 1] = baseColorObj.g;
      colors[idx3 + 2] = baseColorObj.b;

      particleIdx++;
    }
  };

  // Body Structure Geometry Clusters:
  // Head (y = 4.2, r = 0.5)
  addCluster(0, 4.2, 0, 0.45, 0.55, 0.45, 220);

  // Spine & Torso (y = 2.4, r = 0.75x1.2)
  addCluster(0, 2.7, 0, 0.70, 1.10, 0.50, 450);

  // Shoulders & Chest Core (y = 3.3)
  addCluster(-0.85, 3.4, 0, 0.35, 0.35, 0.35, 120);
  addCluster(0.85, 3.4, 0, 0.35, 0.35, 0.35, 120);

  // Arms (Left & Right)
  addCluster(-1.25, 2.4, 0, 0.25, 0.85, 0.25, 180);
  addCluster(1.25, 2.4, 0, 0.25, 0.85, 0.25, 180);

  // Legs & Base Aura (Left & Right)
  addCluster(-0.55, 1.0, 0, 0.30, 1.10, 0.30, 160);
  addCluster(0.55, 1.0, 0, 0.30, 1.10, 0.30, 160);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  // Particle Material with Additive Blending for Neon Glow
  const particleMaterial = new THREE.PointsMaterial({
    size: 0.22,
    vertexColors: true,
    transparent: true,
    opacity: 0.90,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  const bodyPoints = new THREE.Points(geometry, particleMaterial);
  bodyPoints.name = 'avatarBodyPoints';
  avatarGroup.add(bodyPoints);

  // 2. Glowing Chest Energy Core Orb
  const coreGeo = new THREE.IcosahedronGeometry(0.35, 2);
  const coreMat = new THREE.MeshStandardMaterial({
    color: initialColor,
    emissive: initialColor,
    emissiveIntensity: 1.5,
    wireframe: true
  });
  const chestCore = new THREE.Mesh(coreGeo, coreMat);
  chestCore.position.set(0, 3.1, 0);
  chestCore.name = 'chestEnergyCore';
  avatarGroup.add(chestCore);

  // 3. Audio Beat Floor Shockwave Ring System
  const shockwaveGeo = new THREE.RingGeometry(0.5, 0.65, 32);
  const shockwaveMat = new THREE.MeshBasicMaterial({
    color: initialColor,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  });
  const shockwaveMesh = new THREE.Mesh(shockwaveGeo, shockwaveMat);
  shockwaveMesh.rotation.x = -Math.PI * 0.5;
  shockwaveMesh.position.y = 0.02;
  shockwaveMesh.name = 'floorShockwave';
  avatarGroup.add(shockwaveMesh);

  // Store metadata in userData
  avatarGroup.userData = {
    activeForm: initialForm,
    basePositions,
    nodeCount: particleIdx,
    bodyPoints,
    chestCore,
    floorShockwave: shockwaveMesh,
    baseColor: baseColorObj,
    pulseTimer: 0
  };

  return avatarGroup;
}

/**
 * Updates 3D Cyber Particle Avatar motion, shape morphing & audio reactivity per frame.
 * 
 * @param {THREE.Group} avatarGroup 
 * @param {Uint8Array|null} frequencyData - Web Audio API byte frequencies
 * @param {number} deltaTime 
 * @param {number} elapsedTime 
 * @param {number} beatPulse 
 */
export function updateAvatarEntity(avatarGroup, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0.0) {
  if (!avatarGroup || !avatarGroup.userData || !avatarGroup.userData.bodyPoints) return;

  const { bodyPoints, chestCore, floorShockwave, basePositions, nodeCount, activeForm } = avatarGroup.userData;

  const posAttr = bodyPoints.geometry.attributes.position;
  const array = posAttr.array;

  // Extract Audio Frequency Band Energies
  let bassEnergy = beatPulse;
  let midEnergy = 0.0;
  let highEnergy = 0.0;

  if (frequencyData && frequencyData.length > 0) {
    const len = frequencyData.length;
    let bSum = 0, mSum = 0, hSum = 0;

    for (let i = 0; i < Math.floor(len * 0.15); i++) bSum += frequencyData[i];
    for (let i = Math.floor(len * 0.15); i < Math.floor(len * 0.5); i++) mSum += frequencyData[i];
    for (let i = Math.floor(len * 0.5); i < len; i++) hSum += frequencyData[i];

    bassEnergy = Math.max(beatPulse, (bSum / (len * 0.15 * 255.0)));
    midEnergy = mSum / (len * 0.35 * 255.0);
    highEnergy = hSum / (len * 0.5 * 255.0);
  }

  // 1. Dynamic Shape Morphing according to Active Entity Form
  for (let i = 0; i < nodeCount; i++) {
    const idx3 = i * 3;
    const bx = basePositions[idx3];
    const by = basePositions[idx3 + 1];
    const bz = basePositions[idx3 + 2];

    let targetX = bx;
    let targetY = by;
    let targetZ = bz;

    if (activeForm === 'CYBER_KINETIC_HUMANOID') {
      // Energetic Kinetic Warrior: Chest pulse & explosive beat displacement
      const wave = Math.sin(by * 3.0 + elapsedTime * 8.0) * (0.12 + bassEnergy * 0.35);
      targetX = bx * (1.0 + wave);
      targetZ = bz * (1.0 + wave);
    } else if (activeForm === 'EUPHORIC_DANCER_AVATAR') {
      // Euphoric Happy Dancer: Fluid floating spiral wave
      const spiral = Math.sin(by * 2.0 + elapsedTime * 4.0) * 0.25;
      targetX = bx + spiral;
      targetY = by + Math.cos(elapsedTime * 2.0 + bx) * 0.15;
    } else if (activeForm === 'ASTRAL_HOLOGRAM_ENTITY') {
      // Calm Holographic Meditation Avatar: Floating in space with soft pulse
      targetY = by + Math.sin(elapsedTime * 1.5) * 0.18;
      targetX = bx * (1.0 + Math.sin(elapsedTime * 2.0 + by) * 0.05);
    } else if (activeForm === 'GHOST_WIREFRAME_SPIRIT') {
      // Melancholic Ghost Spirit: Dissolving particles floating upwards
      const floatUp = (elapsedTime * 0.8 + i * 0.01) % 4.5;
      targetY = (by + floatUp) % 5.0;
      targetX = bx + Math.sin(elapsedTime + by) * 0.25;
    }

    // Smoothly lerp particle position
    array[idx3] = THREE.MathUtils.lerp(array[idx3], targetX, deltaTime * 12.0);
    array[idx3 + 1] = THREE.MathUtils.lerp(array[idx3 + 1], targetY, deltaTime * 12.0);
    array[idx3 + 2] = THREE.MathUtils.lerp(array[idx3 + 2], targetZ, deltaTime * 12.0);
  }

  posAttr.needsUpdate = true;

  // 2. Chest Energy Core Reaction
  if (chestCore) {
    chestCore.rotation.y = elapsedTime * 2.0;
    chestCore.rotation.x = elapsedTime * 1.2;
    const coreScale = 1.0 + (bassEnergy * 0.65);
    chestCore.scale.set(coreScale, coreScale, coreScale);
  }

  // 3. Floor Shockwave Ring Expansion on Beat Hit
  if (floorShockwave) {
    if (bassEnergy > 0.35) {
      floorShockwave.scale.set(1.0 + bassEnergy * 4.5, 1.0 + bassEnergy * 4.5, 1.0);
      floorShockwave.material.opacity = 0.90;
    } else {
      floorShockwave.scale.set(
        THREE.MathUtils.lerp(floorShockwave.scale.x, 1.0, deltaTime * 6.0),
        THREE.MathUtils.lerp(floorShockwave.scale.y, 1.0, deltaTime * 6.0),
        1.0
      );
      floorShockwave.material.opacity = THREE.MathUtils.lerp(floorShockwave.material.opacity, 0.20, deltaTime * 6.0);
    }
  }

  // Gentle idle hovering of entire avatar group
  avatarGroup.position.y = Math.sin(elapsedTime * 1.2) * 0.08;
  avatarGroup.rotation.y = Math.sin(elapsedTime * 0.4) * 0.15;
}

/**
 * Updates color and entity form of 3D Avatar cleanly.
 * 
 * @param {THREE.Group} avatarGroup 
 * @param {string} entityForm 
 * @param {number|THREE.Color} colorVal 
 */
export function setAvatarEntityState(avatarGroup, entityForm, colorVal) {
  if (!avatarGroup || !avatarGroup.userData) return;

  if (entityForm) {
    avatarGroup.userData.activeForm = entityForm;
  }

  if (colorVal !== undefined) {
    const targetColor = new THREE.Color(colorVal);
    avatarGroup.userData.baseColor = targetColor;

    const { bodyPoints, chestCore, floorShockwave } = avatarGroup.userData;

    if (bodyPoints && bodyPoints.geometry) {
      const colorAttr = bodyPoints.geometry.attributes.color;
      const array = colorAttr.array;
      for (let i = 0; i < colorAttr.count; i++) {
        array[i * 3] = targetColor.r;
        array[i * 3 + 1] = targetColor.g;
        array[i * 3 + 2] = targetColor.b;
      }
      colorAttr.needsUpdate = true;
    }

    if (chestCore && chestCore.material) {
      chestCore.material.color.set(targetColor);
      chestCore.material.emissive.set(targetColor);
    }

    if (floorShockwave && floorShockwave.material) {
      floorShockwave.material.color.set(targetColor);
    }
  }
}
