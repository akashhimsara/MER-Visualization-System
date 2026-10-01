import * as THREE from 'three';

/**
 * Default motion parameters.
 */
export const DEFAULT_MOTION = {
  speed: 1.0,
  intensity: 1.0
};

/**
 * Initializes motion configuration on a particle system.
 * @param {THREE.Points} particles 
 * @param {object} config - { speed, intensity }
 */
export function initParticleMotion(particles, config = {}) {
  if (!particles) return;
  particles.userData.motionConfig = {
    speed: config.speed !== undefined ? config.speed : DEFAULT_MOTION.speed,
    intensity: config.intensity !== undefined ? config.intensity : DEFAULT_MOTION.intensity
  };
}

/**
 * Sets the particle motion speed multiplier.
 * @param {THREE.Points} particles 
 * @param {number} speed - Speed multiplier
 */
export function setMotionSpeed(particles, speed = 1.0) {
  if (!particles || !particles.userData) return;
  if (!particles.userData.motionConfig) {
    initParticleMotion(particles);
  }
  particles.userData.motionConfig.speed = Math.max(0.1, speed);
}

/**
 * Sets the particle motion intensity multiplier.
 * @param {THREE.Points} particles 
 * @param {number} intensity - Intensity multiplier
 */
export function setMotionIntensity(particles, intensity = 1.0) {
  if (!particles || !particles.userData) return;
  if (!particles.userData.motionConfig) {
    initParticleMotion(particles);
  }
  particles.userData.motionConfig.intensity = Math.max(0.0, intensity);
}

/**
 * Updates Ambient Stardust Motes floating motion around the liquid sphere.
 * 
 * @param {THREE.Points} particles - Stardust particle system
 * @param {number} elapsedTime - Total elapsed time in seconds
 * @param {number} deltaTime - Frame delta time
 */
export function updateParticleMotion(particles, elapsedTime = 0, deltaTime = 0.016) {
  if (!particles || !particles.geometry || !particles.userData || !particles.userData.initialPositions) return;

  const positions = particles.geometry.attributes.position.array;
  const initialPositions = particles.userData.initialPositions;
  const count = particles.userData.count || 250;
  const config = particles.userData.motionConfig || DEFAULT_MOTION;

  const speed = config.speed || 1.0;
  const intensity = config.intensity || 1.0;
  const time = elapsedTime * 0.4 * speed;

  for (let i = 0; i < count; i++) {
    const idx = i * 3;
    const ix = initialPositions[idx];
    const iy = initialPositions[idx + 1];
    const iz = initialPositions[idx + 2];

    // Smooth organic 3D floating drift
    positions[idx] = ix + Math.sin(time + iy * 0.5) * 0.4 * intensity;
    positions[idx + 1] = iy + Math.cos(time * 0.8 + ix * 0.5) * 0.3 * intensity;
    positions[idx + 2] = iz + Math.sin(time * 0.6 + iz * 0.5) * 0.4 * intensity;
  }

  particles.geometry.attributes.position.needsUpdate = true;
  particles.rotation.y = elapsedTime * 0.03 * speed;
}

