import * as THREE from 'three';

/**
 * Generates a soft radial alpha texture for silky, glowing stardust particles.
 * Eliminates harsh WebGL square block pixels.
 * @returns {THREE.CanvasTexture}
 */
function createGalaxyParticleTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');

  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
  gradient.addColorStop(0.25, 'rgba(255, 255, 255, 0.75)');
  gradient.addColorStop(0.6, 'rgba(255, 255, 255, 0.18)');
  gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

/**
 * Creates 40,000 Ultra-Fine Soft Glowing Stardust Nebula System around the Liquid Chrome Core.
 * Tomorrowland mainstage festival quality particle galaxy with soft HSL color gradients and zero blocky pixels.
 * 
 * @param {number} count - Particle count (default: 40,000)
 * @param {number|THREE.Color} initialColor - Hex color (default: 0x00f3ff)
 * @returns {THREE.Points} 40,000 Fine Particle Galaxy System
 */
export function create50KGalaxy(count = 28000, initialColor = 0x00f3ff) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const basePositions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const scales = new Float32Array(count);
  const flowSeeds = new Float32Array(count * 3);

  const colorCyan = new THREE.Color(0x00f3ff);   // Cyber Cyan
  const colorMagenta = new THREE.Color(0xff00a0);// Electric Magenta
  const colorPurple = new THREE.Color(0x8800ff); // Royal Purple
  const colorGold = new THREE.Color(0xffaa00);   // Sun Gold

  const innerRadius = 2.0;
  const outerRadius = 13.0;

  for (let i = 0; i < count; i++) {
    const idx3 = i * 3;

    // 4-Arm Spiral Galaxy distribution with smooth Gaussian height dispersion
    const arms = 6;
    const armAngle = (i % arms) * ((Math.PI * 2) / arms);
    const radius = innerRadius + Math.pow(Math.random(), 1.5) * (outerRadius - innerRadius);
    const spinAngle = radius * 0.34;
    const angle = armAngle + spinAngle + (Math.random() - 0.5) * 0.19;

    const x = Math.cos(angle) * radius;
    const y = (Math.random() - 0.5) * (radius * 0.065);
    const z = Math.sin(angle) * radius;

    positions[idx3] = x;
    positions[idx3 + 1] = y;
    positions[idx3 + 2] = z;

    basePositions[idx3] = x;
    basePositions[idx3 + 1] = y;
    basePositions[idx3 + 2] = z;

    // Smooth HSL color transition along spiral radius: Cyan -> Magenta -> Purple -> Gold accents
    const normRad = (radius - innerRadius) / (outerRadius - innerRadius);
    let particleColor;

    if (normRad < 0.35) {
      particleColor = colorCyan.clone().lerp(colorMagenta, normRad / 0.35);
    } else if (normRad < 0.75) {
      particleColor = colorMagenta.clone().lerp(colorPurple, (normRad - 0.35) / 0.40);
    } else {
      particleColor = colorPurple.clone().lerp(colorGold, (normRad - 0.75) / 0.25);
    }

    colors[idx3] = particleColor.r;
    colors[idx3 + 1] = particleColor.g;
    colors[idx3 + 2] = particleColor.b;

    scales[i] = 0.08 + Math.random() * 0.12;
    flowSeeds[idx3] = armAngle;
    flowSeeds[idx3 + 1] = radius;
    flowSeeds[idx3 + 2] = (Math.random() - 0.5) * 0.19;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('scale', new THREE.BufferAttribute(scales, 1));
  geometry.setAttribute('flowSeed', new THREE.BufferAttribute(flowSeeds, 3));

  const particleTexture = createGalaxyParticleTexture();

  const material = new THREE.PointsMaterial({
    size: 0.12, // Soft glowing stardust particle point sizing
    map: particleTexture,
    vertexColors: true,
    transparent: true,
    opacity: 0.60,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  const galaxyPoints = new THREE.Points(geometry, material);
  galaxyPoints.name = '50kCosmicGalaxy';
  galaxyPoints.position.y = 1.45;
  galaxyPoints.position.z = -1.4;
  galaxyPoints.rotation.x = 0.74;
  galaxyPoints.userData = {
    basePositions,
    count,
    outerRadius,
    rotationSpeed: 0.025,
    flowSeeds,
    energyPulse: 0
  };

  return galaxyPoints;
}

/**
 * Updates 40,000 Particle Galaxy spiral rotation & audio reactivity per frame.
 * @param {THREE.Points} galaxyPoints 
 * @param {Uint8Array|null} frequencyData 
 * @param {number} deltaTime 
 * @param {number} elapsedTime 
 * @param {number} beatPulse 
 */
export function update50KGalaxy(galaxyPoints, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0.0) {
  if (!galaxyPoints || !galaxyPoints.userData) return;

  const { rotationSpeed, flowSeeds, outerRadius } = galaxyPoints.userData;
  let bass = beatPulse;
  let mid = 0.18;
  if (frequencyData?.length) {
    const bassEnd = Math.max(1, Math.floor(frequencyData.length * 0.16));
    const midEnd = Math.floor(frequencyData.length * 0.58);
    let bassSum = 0; let midSum = 0;
    for (let index = 0; index < bassEnd; index++) bassSum += frequencyData[index];
    for (let index = bassEnd; index < midEnd; index++) midSum += frequencyData[index];
    bass = Math.max(beatPulse, bassSum / (bassEnd * 255));
    mid = midSum / Math.max(1, (midEnd - bassEnd) * 255);
  }
  galaxyPoints.userData.energyPulse += (bass - galaxyPoints.userData.energyPulse) * Math.min(1, deltaTime * 8);

  galaxyPoints.rotation.z += (rotationSpeed + bass * 0.16) * deltaTime;
  galaxyPoints.rotation.x = 0.74 + Math.sin(elapsedTime * 0.16) * 0.035;

  const targetScale = 1.0 + (beatPulse * 0.14);
  galaxyPoints.scale.set(targetScale, targetScale, targetScale);

  // Moving energy lanes: a visible pulse travels outward from the core on each beat.
  const positions = galaxyPoints.geometry.attributes.position.array;
  for (let index = 0; index < galaxyPoints.geometry.attributes.position.count; index++) {
    const arm = flowSeeds[index * 3];
    const radius = flowSeeds[index * 3 + 1];
    const jitter = flowSeeds[index * 3 + 2];
    const travel = Math.sin(radius * 1.55 - elapsedTime * (2.2 + bass * 4.0));
    const ripple = Math.max(0, travel) * (0.08 + galaxyPoints.userData.energyPulse * 0.38);
    const flowRadius = radius + ripple * (1.0 + radius / outerRadius * 1.6);
    const angle = arm + flowRadius * 0.34 + jitter + Math.sin(elapsedTime * 0.35 + radius) * mid * 0.10;
    positions[index * 3] = Math.cos(angle) * flowRadius;
    positions[index * 3 + 1] = Math.sin(radius * 0.55 + elapsedTime * 0.6) * (0.06 + mid * 0.12) + jitter * 1.8;
    positions[index * 3 + 2] = Math.sin(angle) * flowRadius;
  }
  galaxyPoints.geometry.attributes.position.needsUpdate = true;
}

/**
 * Updates 40,000 Particle Galaxy colors dynamically based on AI emotion mapping.
 * @param {THREE.Points} galaxyPoints 
 * @param {number|THREE.Color} primary 
 */
export function set50KGalaxyColor(galaxyPoints, primary) {
  if (!galaxyPoints || !galaxyPoints.geometry) return;

  const targetColor = new THREE.Color(primary);
  const secColor = targetColor.clone().offsetHSL(0.35, 0, 0);
  const colorAttr = galaxyPoints.geometry.attributes.color;
  const array = colorAttr.array;

  for (let i = 0; i < colorAttr.count; i++) {
    const idx3 = i * 3;
    const mixFactor = (i % 100) / 100.0;
    array[idx3] = targetColor.r + ((secColor.r - targetColor.r) * mixFactor);
    array[idx3 + 1] = targetColor.g + ((secColor.g - targetColor.g) * mixFactor);
    array[idx3 + 2] = targetColor.b + ((secColor.b - targetColor.b) * mixFactor);
  }
  colorAttr.needsUpdate = true;
}
