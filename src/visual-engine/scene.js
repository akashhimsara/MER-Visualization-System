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

  // 1. Dark Glossy Reflective Mirror Floor Surface
  const floorGeo = new THREE.PlaneGeometry(60, 60);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x04060d,
    roughness: 0.15,
    metalness: 0.90,
    side: THREE.DoubleSide
  });
  const floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotation.x = -Math.PI * 0.5; // Horizontal floor
  floorMesh.position.y = 0.0;
  floorMesh.name = 'reflectiveFloor';
  scene.add(floorMesh);

  // 2. Central 3D Circular Equalizer Ring System
  const spectrumRing = createSpectrumRing();
  spectrumRing.position.set(0, 0, 0);
  scene.add(spectrumRing);

  // Empty placeholder group container for engine backwards compatibility
  const placeholderMesh = new THREE.Group();
  scene.add(placeholderMesh);

  return { scene, placeholderMesh, spectrumRing, floorMesh };
}

