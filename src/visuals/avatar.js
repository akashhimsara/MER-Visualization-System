import * as THREE from 'three';

/**
 * Creates 3D Holographic Kinetic Avatar & Dynamic Entity System (Tomorrowland Festival Quality).
 * Features a sleek multi-faceted 3D wireframe android structure, inner pulsing plasma heart,
 * dual counter-rotating laser rings, and floor shockwaves with ZERO overexposed yellow blobs.
 * 
 * @param {string} initialForm - 'CYBER_KINETIC_HUMANOID' | 'EUPHORIC_DANCER_AVATAR' | 'ASTRAL_HOLOGRAM_ENTITY' | 'GHOST_WIREFRAME_SPIRIT'
 * @param {number|string|THREE.Color} initialColor - Hex color (default: 0x00f3ff)
 * @returns {THREE.Group} Group containing 3D Avatar Entity
 */
export function create3DAvatarEntity(initialForm = 'CYBER_KINETIC_HUMANOID', initialColor = 0x00f3ff) {
  const avatarGroup = new THREE.Group();
  avatarGroup.name = '3dAvatarEntity';

  const baseColor = new THREE.Color(initialColor);

  // 1. Sleek Precision Head Crystal Facet
  const headGeo = new THREE.IcosahedronGeometry(0.55, 1);
  const headMat = new THREE.MeshStandardMaterial({
    color: baseColor,
    emissive: 0x002244,
    emissiveIntensity: 0.5,
    roughness: 0.1,
    metalness: 0.95,
    wireframe: true
  });
  const headMesh = new THREE.Mesh(headGeo, headMat);
  headMesh.position.set(0, 3.8, 0);
  headMesh.name = 'avatarHead';
  avatarGroup.add(headMesh);

  // 2. Multi-Faceted Cyber Torso Architecture
  const torsoGeo = new THREE.OctahedronGeometry(1.15, 2);
  const torsoMat = new THREE.MeshStandardMaterial({
    color: baseColor,
    emissive: 0x001122,
    emissiveIntensity: 0.4,
    roughness: 0.15,
    metalness: 0.9,
    wireframe: true
  });
  const torsoMesh = new THREE.Mesh(torsoGeo, torsoMat);
  torsoMesh.position.set(0, 2.5, 0);
  torsoMesh.scale.set(0.85, 1.3, 0.65);
  torsoMesh.name = 'avatarTorso';
  avatarGroup.add(torsoMesh);

  // 3. Glowing Inner Heart Plasma Core Orb
  const coreGeo = new THREE.IcosahedronGeometry(0.35, 2);
  const coreMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  });
  const chestCore = new THREE.Mesh(coreGeo, coreMat);
  chestCore.position.set(0, 2.65, 0);
  chestCore.name = 'chestEnergyCore';
  avatarGroup.add(chestCore);

  // 4. Dual Counter-Rotating Orbital Laser Rings around Avatar Body
  const ring1Geo = new THREE.TorusGeometry(1.6, 0.03, 16, 64);
  const ring1Mat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending });
  const ring1Mesh = new THREE.Mesh(ring1Geo, ring1Mat);
  ring1Mesh.rotation.x = Math.PI * 0.4;
  ring1Mesh.position.y = 2.6;
  avatarGroup.add(ring1Mesh);

  const ring2Geo = new THREE.TorusGeometry(2.1, 0.03, 16, 64);
  const ring2Mat = new THREE.MeshBasicMaterial({ color: 0xff00a0, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending });
  const ring2Mesh = new THREE.Mesh(ring2Geo, ring2Mat);
  ring2Mesh.rotation.y = Math.PI * 0.4;
  ring2Mesh.position.y = 2.6;
  avatarGroup.add(ring2Mesh);

  // 5. Fine Stardust Constellation Particles orbiting Avatar
  const stardustCount = 180;
  const stardustGeo = new THREE.BufferGeometry();
  const stardustPositions = new Float32Array(stardustCount * 3);
  for (let s = 0; s < stardustCount; s++) {
    const angle = Math.random() * Math.PI * 2;
    const rad = 1.2 + Math.random() * 1.8;
    stardustPositions[s * 3] = Math.cos(angle) * rad;
    stardustPositions[s * 3 + 1] = 1.0 + Math.random() * 3.5;
    stardustPositions[s * 3 + 2] = Math.sin(angle) * rad;
  }
  stardustGeo.setAttribute('position', new THREE.BufferAttribute(stardustPositions, 3));
  const stardustMat = new THREE.PointsMaterial({
    color: baseColor,
    size: 0.12,
    transparent: true,
    opacity: 0.75,
    blending: THREE.AdditiveBlending
  });
  const stardustPoints = new THREE.Points(stardustGeo, stardustMat);
  avatarGroup.add(stardustPoints);

  // 6. Audio Beat Floor Laser Shockwave Ring System
  const shockwaveGeo = new THREE.RingGeometry(0.8, 0.95, 32);
  const shockwaveMat = new THREE.MeshBasicMaterial({
    color: baseColor,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.80,
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
    headMesh,
    torsoMesh,
    chestCore,
    ring1Mesh,
    ring2Mesh,
    stardustPoints,
    floorShockwave: shockwaveMesh,
    baseColor
  };

  return avatarGroup;
}

/**
 * Updates 3D Holographic Kinetic Avatar motion, shape morphing & audio reactivity per frame.
 * 
 * @param {THREE.Group} avatarGroup 
 * @param {Uint8Array|null} frequencyData - Web Audio API byte frequencies
 * @param {number} deltaTime 
 * @param {number} elapsedTime 
 * @param {number} beatPulse 
 */
export function updateAvatarEntity(avatarGroup, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0.0) {
  if (!avatarGroup || !avatarGroup.userData) return;

  const { headMesh, torsoMesh, chestCore, ring1Mesh, ring2Mesh, stardustPoints, floorShockwave, activeForm } = avatarGroup.userData;

  // Extract Audio Frequency Band Energies
  let bassEnergy = beatPulse;
  let midEnergy = 0.0;

  if (frequencyData && frequencyData.length > 0) {
    const len = frequencyData.length;
    let bSum = 0, mSum = 0;
    for (let i = 0; i < Math.floor(len * 0.15); i++) bSum += frequencyData[i];
    for (let i = Math.floor(len * 0.15); i < Math.floor(len * 0.5); i++) mSum += frequencyData[i];

    bassEnergy = Math.max(beatPulse, (bSum / (len * 0.15 * 255.0)));
    midEnergy = mSum / (len * 0.35 * 255.0);
  }

  // 1. Sleek Head & Torso Rotation and Hovering
  if (headMesh) {
    headMesh.rotation.y = elapsedTime * 0.5;
    headMesh.rotation.x = Math.sin(elapsedTime * 1.5) * 0.1;
  }
  if (torsoMesh) {
    torsoMesh.rotation.y = -elapsedTime * 0.3;
    const torsoScale = 1.0 + (bassEnergy * 0.12);
    torsoMesh.scale.set(0.85 * torsoScale, 1.3 * torsoScale, 0.65 * torsoScale);
  }

  // 2. Chest Energy Core Reaction
  if (chestCore) {
    chestCore.rotation.y = elapsedTime * 2.5;
    chestCore.rotation.x = elapsedTime * 1.5;
    const coreScale = 1.0 + (bassEnergy * 0.75);
    chestCore.scale.set(coreScale, coreScale, coreScale);
  }

  // 3. Counter-Rotating Orbital Rings
  if (ring1Mesh) ring1Mesh.rotation.z = elapsedTime * 0.9;
  if (ring2Mesh) ring2Mesh.rotation.z = -elapsedTime * 0.7;

  // 4. Stardust Orbit Movement
  if (stardustPoints) {
    stardustPoints.rotation.y = elapsedTime * 0.25;
  }

  // 5. Floor Shockwave Ring Expansion on Beat Hit
  if (floorShockwave) {
    if (bassEnergy > 0.35) {
      floorShockwave.scale.set(1.0 + bassEnergy * 4.0, 1.0 + bassEnergy * 4.0, 1.0);
      floorShockwave.material.opacity = 0.85;
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
  avatarGroup.position.y = Math.sin(elapsedTime * 1.2) * 0.10;
}

/**
 * Updates color and entity form of 3D Avatar cleanly with crisp HSL palette.
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

    const { headMesh, torsoMesh, chestCore, ring1Mesh, ring2Mesh, stardustPoints, floorShockwave } = avatarGroup.userData;

    if (headMesh && headMesh.material) headMesh.material.color.lerp(targetColor, 0.3);
    if (torsoMesh && torsoMesh.material) torsoMesh.material.color.lerp(targetColor, 0.3);
    if (chestCore && chestCore.material) chestCore.material.color.lerp(targetColor, 0.3);
    if (ring1Mesh && ring1Mesh.material) ring1Mesh.material.color.lerp(targetColor, 0.3);
    if (stardustPoints && stardustPoints.material) stardustPoints.material.color.lerp(targetColor, 0.3);
    if (floorShockwave && floorShockwave.material) floorShockwave.material.color.lerp(targetColor, 0.3);
  }
}
