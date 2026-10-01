import * as THREE from 'three';

/**
 * Creates and configures the Perspective Camera.
 * @param {number} width - Viewport width
 * @param {number} height - Viewport height
 * @returns {THREE.PerspectiveCamera}
 */
export function createCamera(width, height) {
  const fov = 50;
  const aspect = width / height;
  const near = 0.1;
  const far = 1000;

  const camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
  camera.userData = { baseFov: fov };
  // Immersive 3D perspective looking over 3D equalizer ring & mirror floor
  camera.position.set(0, 4.0, 7.2);
  camera.lookAt(0, 0.6, 0);
  return camera;
}

/**
 * Updates camera aspect ratio on window resize.
 * @param {THREE.PerspectiveCamera} camera 
 * @param {number} width 
 * @param {number} height 
 */
export function updateCameraAspect(camera, width, height) {
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
