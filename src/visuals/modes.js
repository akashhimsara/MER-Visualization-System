import * as THREE from 'three';
import { createEqualizerRing, updateSpectrumRing } from './spectrum.js';

/**
 * Visual Mode Key Constants
 */
export const VISUAL_MODES = {
  EQUALIZER_RING: 'EQUALIZER_RING',     // Mode 1: 64 3D Glass Equalizer Bar Towers (HAPPY/Default)
  NEON_TUNNEL: 'NEON_TUNNEL',           // Mode 2: 36 3D Flying Cyberpunk Neon Laser Tunnel (ENERGETIC)
  HOLOGRAPHIC_CORE: 'HOLOGRAPHIC_CORE', // Mode 3: Faceted Crystal Core & Orbital Spectrum Rings (CALM)
  HORIZON_GRID: 'HORIZON_GRID'          // Mode 4: 3D Audio Wireframe Ground Grid (SAD)
};

/**
 * Creates 3D Cyberpunk Neon Flying Tunnel Mesh Group.
 */
function createTunnelMeshGroup() {
  const tunnelGroup = new THREE.Group();
  tunnelGroup.name = 'mode_neonTunnel';

  const ringCount = 30;
  const tunnelLength = 50;
  const zStep = tunnelLength / ringCount;
  const rings = [];

  for (let i = 0; i < ringCount; i++) {
    const zPos = 5.0 - (i * zStep);
    const radius = 3.6;
    const isEven = i % 2 === 0;

    const ringGeo = new THREE.RingGeometry(radius - 0.16, radius, 6);
    const ringMat = new THREE.MeshBasicMaterial({
      color: isEven ? 0x00f3ff : 0xff00a0,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.set(0, 0, zPos);
    ringMesh.rotation.z = (i / ringCount) * Math.PI;
    tunnelGroup.add(ringMesh);

    rings.push({ mesh: ringMesh, zPos, index: i });
  }

  tunnelGroup.userData = { rings, tunnelLength };
  return tunnelGroup;
}

/**
 * Creates 3D Holographic Crystal Core & Dual Orbital Rings Group.
 */
function createHolographicCoreGroup() {
  const group = new THREE.Group();
  group.name = 'mode_holographicCore';

  // Faceted Crystal Core Orb
  const coreGeo = new THREE.IcosahedronGeometry(1.2, 2);
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0x00f3ff,
    emissive: 0x004488,
    emissiveIntensity: 0.6,
    roughness: 0.1,
    metalness: 0.9,
    wireframe: true
  });
  const coreMesh = new THREE.Mesh(coreGeo, coreMat);
  coreMesh.name = 'coreMesh';
  group.add(coreMesh);

  // Orbital Ring A
  const ringAGeo = new THREE.TorusGeometry(2.2, 0.04, 16, 100);
  const ringAMat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.85 });
  const ringAMesh = new THREE.Mesh(ringAGeo, ringAMat);
  ringAMesh.name = 'ringAMesh';
  ringAMesh.rotation.x = Math.PI * 0.45;
  group.add(ringAMesh);

  // Orbital Ring B
  const ringBGeo = new THREE.TorusGeometry(2.8, 0.04, 16, 100);
  const ringBMat = new THREE.MeshBasicMaterial({ color: 0xff00aa, transparent: true, opacity: 0.85 });
  const ringBMesh = new THREE.Mesh(ringBGeo, ringBMat);
  ringBMesh.name = 'ringBMesh';
  ringBMesh.rotation.y = Math.PI * 0.45;
  group.add(ringBMesh);

  group.userData = { coreMesh, ringAMesh, ringBMesh };
  return group;
}

/**
 * Creates 3D Wireframe Ground Audio Grid.
 */
function createHorizonGridGroup() {
  const group = new THREE.Group();
  group.name = 'mode_horizonGrid';

  const gridGeo = new THREE.PlaneGeometry(50, 50, 40, 40);
  const gridMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    wireframe: true,
    transparent: true,
    opacity: 0.6
  });
  const gridMesh = new THREE.Mesh(gridGeo, gridMat);
  gridMesh.rotation.x = -Math.PI * 0.5;
  gridMesh.position.y = 0.0;
  group.add(gridMesh);

  group.userData = { gridMesh };
  return group;
}

/**
 * VisualModeManager controls instantiation, audio updates, and smooth switching
 * between 3D Visualizer Modes.
 */
export class VisualModeManager {
  constructor(scene) {
    this.scene = scene;
    this.activeMode = VISUAL_MODES.EQUALIZER_RING;

    this.modes = {
      [VISUAL_MODES.EQUALIZER_RING]: createEqualizerRing(64, 3.6),
      [VISUAL_MODES.NEON_TUNNEL]: createTunnelMeshGroup(),
      [VISUAL_MODES.HOLOGRAPHIC_CORE]: createHolographicCoreGroup(),
      [VISUAL_MODES.HORIZON_GRID]: createHorizonGridGroup()
    };

    // Mount all modes into Three.js scene
    Object.keys(this.modes).forEach(modeKey => {
      const modeGroup = this.modes[modeKey];
      modeGroup.visible = (modeKey === this.activeMode);
      this.scene.add(modeGroup);
    });
  }

  /**
   * Switches active 3D Visualizer Mode smoothly.
   * @param {string} modeKey - 'EQUALIZER_RING' | 'NEON_TUNNEL' | 'HOLOGRAPHIC_CORE' | 'HORIZON_GRID'
   */
  switchMode(modeKey) {
    if (!this.modes[modeKey]) return;

    this.activeMode = modeKey;

    Object.keys(this.modes).forEach(k => {
      this.modes[k].visible = (k === this.activeMode);
    });
  }

  /**
   * Automatically selects 3D Visual Mode based on AI predicted emotion category.
   * @param {string} emotionCategory - 'HAPPY' | 'ENERGETIC' | 'CALM' | 'SAD'
   */
  setModeFromEmotion(emotionCategory) {
    const cat = String(emotionCategory).toUpperCase();
    if (cat === 'ENERGETIC') {
      this.switchMode(VISUAL_MODES.NEON_TUNNEL);
    } else if (cat === 'CALM') {
      this.switchMode(VISUAL_MODES.HOLOGRAPHIC_CORE);
    } else if (cat === 'SAD') {
      this.switchMode(VISUAL_MODES.HORIZON_GRID);
    } else {
      this.switchMode(VISUAL_MODES.EQUALIZER_RING);
    }
  }

  /**
   * Updates current active 3D mode geometry & audio reactivity on every animation frame.
   */
  update(frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0.0) {
    const currentGroup = this.modes[this.activeMode];
    if (!currentGroup) return;

    if (this.activeMode === VISUAL_MODES.EQUALIZER_RING) {
      updateSpectrumRing(currentGroup, frequencyData, deltaTime, elapsedTime, beatPulse);
    } else if (this.activeMode === VISUAL_MODES.NEON_TUNNEL) {
      const { rings, tunnelLength } = currentGroup.userData;
      const flySpeed = 6.0 + (beatPulse * 16.0);
      rings.forEach(r => {
        r.mesh.position.z += flySpeed * deltaTime;
        if (r.mesh.position.z > 5.0) r.mesh.position.z -= tunnelLength;
        r.mesh.rotation.z += 0.2 * deltaTime;
      });
    } else if (this.activeMode === VISUAL_MODES.HOLOGRAPHIC_CORE) {
      const { coreMesh, ringAMesh, ringBMesh } = currentGroup.userData;
      if (coreMesh) {
        coreMesh.rotation.y = elapsedTime * 0.4;
        coreMesh.rotation.x = elapsedTime * 0.2;
        const coreScale = 1.0 + (beatPulse * 0.25);
        coreMesh.scale.set(coreScale, coreScale, coreScale);
      }
      if (ringAMesh) ringAMesh.rotation.z = elapsedTime * 0.6;
      if (ringBMesh) ringBMesh.rotation.z = -elapsedTime * 0.5;
    } else if (this.activeMode === VISUAL_MODES.HORIZON_GRID) {
      const { gridMesh } = currentGroup.userData;
      if (gridMesh) {
        gridMesh.position.z = (elapsedTime * 4.0) % 2.5;
      }
    }
  }
}
