import * as THREE from 'three';

/**
 * Default fallback color (Neon Cyan).
 */
export const DEFAULT_COLOR = 0x00f3ff;

/**
 * Sets the color of a particle system material dynamically.
 * Accepts hex numbers (0xff0077), hex strings ('#ff0077'), or THREE.Color instances.
 * 
 * @param {THREE.Points|THREE.Mesh|THREE.Material} target - THREE Object or Material
 * @param {number|string|THREE.Color} colorValue - New color value
 */
export function setParticleColor(target, colorValue) {
  if (!target) return;

  const material = target.material ? target.material : target;
  if (!material || !material.color) return;

  if (colorValue instanceof THREE.Color) {
    material.color.copy(colorValue);
  } else {
    material.color.set(colorValue);
  }
}

/**
 * Smoothly transitions (lerps) the material color towards a target color.
 * 
 * @param {THREE.Points|THREE.Mesh|THREE.Material} target - THREE Object or Material
 * @param {number|string|THREE.Color} targetColor - Destination color
 * @param {number} alpha - Interpolation rate (0.0 to 1.0)
 */
export function lerpParticleColor(target, targetColor, alpha = 0.05) {
  if (!target) return;

  const material = target.material ? target.material : target;
  if (!material || !material.color) return;

  const destination = new THREE.Color(targetColor);
  material.color.lerp(destination, alpha);
}

/**
 * Updates particle size and opacity dynamically.
 * @param {THREE.Points} target 
 * @param {number} size 
 * @param {number} opacity 
 */
export function setParticleStyle(target, size = 0.45, opacity = 0.9) {
  if (!target || !target.material) return;
  target.material.size = THREE.MathUtils.lerp(target.material.size, size, 0.1);
  target.material.opacity = THREE.MathUtils.lerp(target.material.opacity, opacity, 0.1);
}
