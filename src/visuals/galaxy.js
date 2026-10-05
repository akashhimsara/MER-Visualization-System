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
export function create50KGalaxy(count = 40000, initialColor = 0x00f3ff) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const basePositions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const scales = new Float32Array(count);

  const colorCyan = new THREE.Color(0x00f3ff);   // Cyber Cyan
  const colorMagenta = new THREE.Color(0xff00a0);// Electric Magenta
  const colorPurple = new THREE.Color(0x8800ff); // Royal Purple
  const colorGold = new THREE.Color(0xffaa00);   // Sun Gold

  const innerRadius = 2.2;
  const outerRadius = 24.0;

  for (let i = 0; i < count; i++) {
    const idx3 = i * 3;

    // 4-Arm Spiral Galaxy distribution with smooth Gaussian height dispersion
    const arms = 4;
    const armAngle = (i % arms) * ((Math.PI * 2) / arms);
    const radius = innerRadius + Math.pow(Math.random(), 1.5) * (outerRadius - innerRadius);
    const spinAngle = radius * 0.22;
    const angle = armAngle + spinAngle + (Math.random() - 0.5) * 0.35;

    const x = Math.cos(angle) * radius;
    const y = (Math.random() - 0.5) * (radius * 0.18);
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
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('scale', new THREE.BufferAttribute(scales, 1));

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
  galaxyPoints.userData = {
    basePositions,
    count,
    outerRadius,
    rotationSpeed: 0.025
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

  const { rotationSpeed } = galaxyPoints.userData;

  galaxyPoints.rotation.y += (rotationSpeed + beatPulse * 0.06) * deltaTime;
  galaxyPoints.rotation.z = Math.sin(elapsedTime * 0.20) * 0.05;

  const targetScale = 1.0 + (beatPulse * 0.08);
  galaxyPoints.scale.set(targetScale, targetScale, targetScale);
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
    const pColor = targetColor.clone().lerp(secColor, mixFactor);

    array[idx3] = pColor.r;
    array[idx3 + 1] = pColor.g;
    array[idx3 + 2] = pColor.b;
  }
  colorAttr.needsUpdate = true;
}
