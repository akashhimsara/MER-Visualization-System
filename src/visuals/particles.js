import * as THREE from 'three';
import { DEFAULT_COLOR } from './color.js';
import { initParticleMotion, updateParticleMotion } from './animation.js';

/**
 * Creates a soft circular radial glow texture for ambient stardust motes.
 * @returns {THREE.CanvasTexture}
 */
function createStardustTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');

  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
  gradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.7)');
  gradient.addColorStop(0.7, 'rgba(255, 255, 255, 0.15)');
  gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

/**
 * Creates Concept A Ambient Stardust Motes.
 * Delicate glowing particles floating around the 3D Liquid Sphere.
 * 
 * @param {number} count - Number of stardust particles (default: 250)
 * @param {number|string|THREE.Color} initialColor 
 * @returns {THREE.Points} THREE.Points particle system
 */
export function createParticles(count = 250, initialColor = DEFAULT_COLOR) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const scales = new Float32Array(count);
  const initialPositions = new Float32Array(count * 3);

  const range = 18.0;

  for (let i = 0; i < count; i++) {
    const idx = i * 3;
    const x = (Math.random() - 0.5) * range;
    const y = (Math.random() - 0.5) * range * 0.7 + 1.0;
    const z = (Math.random() - 0.5) * range;

    positions[idx] = x;
    positions[idx + 1] = y;
    positions[idx + 2] = z;

    initialPositions[idx] = x;
    initialPositions[idx + 1] = y;
    initialPositions[idx + 2] = z;

    scales[i] = 0.3 + Math.random() * 0.7;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('scale', new THREE.BufferAttribute(scales, 1));

  const material = new THREE.PointsMaterial({
    color: initialColor,
    size: 0.18,
    map: createStardustTexture(),
    transparent: true,
    opacity: 0.65,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  const particles = new THREE.Points(geometry, material);
  particles.name = 'stardustParticles';
  particles.userData = {
    initialPositions,
    count,
    baseSize: 0.35,
    motionConfig: { speed: 1.0, intensity: 1.0 }
  };

  initParticleMotion(particles);
  return particles;
}

/**
 * Delegates particle motion update to the animation module.
 * @param {THREE.Points} particles - Stardust particles object
 * @param {number} time - Current timestamp
 * @param {number} deltaTime - Time delta between frames
 */
export function updateParticles(particles, time = 0, deltaTime = 0.016) {
  updateParticleMotion(particles, time, deltaTime);
}

/**
 * Disposes particle system resources.
 * @param {THREE.Points} particles 
 */
export function disposeParticles(particles) {
  if (!particles) return;
  if (particles.geometry) particles.geometry.dispose();
  if (particles.material) particles.material.dispose();
}

