import * as THREE from 'three';
import { createSpectrumRing } from '../visuals/spectrum.js';

/**
 * Creates and configures the main Three.js Scene.
 * 3D Circular Glass Equalizer Bar Array & Reflective Mirror Floor.
 * 
 * @returns {{ scene: THREE.Scene, placeholderMesh: THREE.Group, spectrumRing: THREE.Group, floorMesh: THREE.Mesh }}
 */
export function createScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x020306); // Pitch dark luxury space

  // Empty placeholder group container for engine backwards compatibility
  const placeholderMesh = new THREE.Group();
  scene.add(placeholderMesh);

  return { scene, placeholderMesh };
}

