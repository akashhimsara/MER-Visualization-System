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
 * Creates High-End 3D Cyberpunk Neon Flying Laser Tunnel with Central Star Matrix.
 */
function createTunnelMeshGroup() {
  const tunnelGroup = new THREE.Group();
  tunnelGroup.name = 'mode_neonTunnel';

  const ringCount = 36;
  const tunnelLength = 60;
  const zStep = tunnelLength / ringCount;
  const rings = [];

  for (let i = 0; i < ringCount; i++) {
    const zPos = 6.0 - (i * zStep);
    const radius = 3.8;
    const isEven = i % 2 === 0;

    // Outer Octagonal Neon Frame Ring
    const ringGeo = new THREE.RingGeometry(radius - 0.20, radius, 8);
    const ringMat = new THREE.MeshBasicMaterial({
      color: isEven ? 0x00f3ff : 0xff00a0,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.set(0, 0, zPos);
    ringMesh.rotation.z = (i / ringCount) * Math.PI;
    tunnelGroup.add(ringMesh);

    // Inner Glowing Laser Node Lines
    const innerGeo = new THREE.TorusGeometry(radius - 0.25, 0.03, 8, 32);
    const innerMat = new THREE.MeshBasicMaterial({
      color: isEven ? 0xff00a0 : 0xaa00ff,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    ringMesh.add(innerMesh);

    rings.push({ mesh: ringMesh, innerMesh, zPos, index: i });
  }

  // Central Hyper-Speed Particle Core Matrix
  const starCount = 300;
  const starGeo = new THREE.BufferGeometry();
  const starPositions = new Float32Array(starCount * 3);
  for (let s = 0; s < starCount; s++) {
    starPositions[s * 3] = (Math.random() - 0.5) * 6.0;
    starPositions[s * 3 + 1] = (Math.random() - 0.5) * 6.0;
    starPositions[s * 3 + 2] = -Math.random() * tunnelLength;
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
  const starMat = new THREE.PointsMaterial({
    color: 0x00f3ff,
    size: 0.25,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  });
  const starPoints = new THREE.Points(starGeo, starMat);
  tunnelGroup.add(starPoints);

  tunnelGroup.userData = { rings, starPoints, tunnelLength };
  return tunnelGroup;
}

/**
 * Creates 3D Holographic Faceted Crystal Core & Dual Orbital Rings Group.
 */
function createHolographicCoreGroup() {
  const group = new THREE.Group();
  group.name = 'mode_holographicCore';

  // 1. Faceted Crystal Core Outer Mesh
  const coreGeo = new THREE.IcosahedronGeometry(1.4, 2);
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0x00f3ff,
    emissive: 0x003366,
    emissiveIntensity: 0.8,
    roughness: 0.1,
    metalness: 0.95,
    wireframe: true
  });
  const coreMesh = new THREE.Mesh(coreGeo, coreMat);
  coreMesh.name = 'coreMesh';
  group.add(coreMesh);

  // 2. Inner Glowing Core Plasma Orb
  const innerOrbGeo = new THREE.SphereGeometry(0.85, 32, 32);
  const innerOrbMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    transparent: true,
    opacity: 0.7,
    blending: THREE.AdditiveBlending
  });
  const innerOrbMesh = new THREE.Mesh(innerOrbGeo, innerOrbMat);
  group.add(innerOrbMesh);

  // 3. Orbital Ring A
  const ringAGeo = new THREE.TorusGeometry(2.4, 0.04, 16, 100);
  const ringAMat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending });
  const ringAMesh = new THREE.Mesh(ringAGeo, ringAMat);
  ringAMesh.name = 'ringAMesh';
  ringAMesh.rotation.x = Math.PI * 0.45;
  group.add(ringAMesh);

  // 4. Orbital Ring B
  const ringBGeo = new THREE.TorusGeometry(3.0, 0.04, 16, 100);
  const ringBMat = new THREE.MeshBasicMaterial({ color: 0xff00aa, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending });
  const ringBMesh = new THREE.Mesh(ringBGeo, ringBMat);
  ringBMesh.name = 'ringBMesh';
  ringBMesh.rotation.y = Math.PI * 0.45;
  group.add(ringBMesh);

  // 5. Orbital Ring C (Outer Horizon Ring)
  const ringCGeo = new THREE.TorusGeometry(3.6, 0.03, 16, 100);
  const ringCMat = new THREE.MeshBasicMaterial({ color: 0xffd700, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending });
  const ringCMesh = new THREE.Mesh(ringCGeo, ringCMat);
  ringCMesh.rotation.x = Math.PI * 0.25;
  group.add(ringCMesh);

  group.userData = { coreMesh, innerOrbMesh, ringAMesh, ringBMesh, ringCMesh };
  return group;
}

/**
 * Creates 3D Audio-Reactive Wireframe Synthwave Ground Grid & Horizon Sun Arc.
 */
function createHorizonGridGroup() {
  const group = new THREE.Group();
  group.name = 'mode_horizonGrid';

  // 1. Dynamic Audio Wireframe Ground Grid Plane (50x50 with 50x50 segments)
  const gridGeo = new THREE.PlaneGeometry(60, 60, 50, 50);
  const gridMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    wireframe: true,
    transparent: true,
    opacity: 0.75,
    blending: THREE.AdditiveBlending
  });
  const gridMesh = new THREE.Mesh(gridGeo, gridMat);
  gridMesh.rotation.x = -Math.PI * 0.5;
  gridMesh.position.y = -0.2;
  group.add(gridMesh);

  // Store initial vertex positions for dynamic audio wave displacement
  const basePositions = new Float32Array(gridGeo.attributes.position.array);

  // 2. Horizon Glowing Sun Arc / Halo
  const sunGeo = new THREE.RingGeometry(4.0, 6.5, 32);
  const sunMat = new THREE.MeshBasicMaterial({
    color: 0x00aaff,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.4,
    blending: THREE.AdditiveBlending
  });
  const sunMesh = new THREE.Mesh(sunGeo, sunMat);
  sunMesh.position.set(0, 3.5, -28);
  group.add(sunMesh);

  group.userData = { gridMesh, gridGeo, basePositions, sunMesh };
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
      const { rings, starPoints, tunnelLength } = currentGroup.userData;
      const flySpeed = 8.0 + (beatPulse * 22.0);

      rings.forEach(r => {
        r.mesh.position.z += flySpeed * deltaTime;
        if (r.mesh.position.z > 6.0) r.mesh.position.z -= tunnelLength;
        r.mesh.rotation.z += (r.index % 2 === 0 ? 0.35 : -0.35) * deltaTime;
        
        // Pulse ring scale on beat hit
        const scale = 1.0 + (beatPulse * 0.18);
        r.mesh.scale.set(scale, scale, 1.0);
      });

      if (starPoints && starPoints.geometry) {
        const posAttr = starPoints.geometry.attributes.position;
        const array = posAttr.array;
        for (let s = 0; s < posAttr.count; s++) {
          array[s * 3 + 2] += flySpeed * 1.5 * deltaTime;
          if (array[s * 3 + 2] > 6.0) array[s * 3 + 2] -= tunnelLength;
        }
        posAttr.needsUpdate = true;
      }
    } else if (this.activeMode === VISUAL_MODES.HOLOGRAPHIC_CORE) {
      const { coreMesh, innerOrbMesh, ringAMesh, ringBMesh, ringCMesh } = currentGroup.userData;
      if (coreMesh) {
        coreMesh.rotation.y = elapsedTime * 0.45;
        coreMesh.rotation.x = elapsedTime * 0.25;
        const coreScale = 1.0 + (beatPulse * 0.30);
        coreMesh.scale.set(coreScale, coreScale, coreScale);
      }
      if (innerOrbMesh) {
        const orbScale = 1.0 + Math.sin(elapsedTime * 3.0) * 0.08 + (beatPulse * 0.20);
        innerOrbMesh.scale.set(orbScale, orbScale, orbScale);
      }
      if (ringAMesh) ringAMesh.rotation.z = elapsedTime * 0.70;
      if (ringBMesh) ringBMesh.rotation.z = -elapsedTime * 0.55;
      if (ringCMesh) ringCMesh.rotation.y = elapsedTime * 0.40;
    } else if (this.activeMode === VISUAL_MODES.HORIZON_GRID) {
      const { gridMesh, gridGeo, basePositions, sunMesh } = currentGroup.userData;

      if (gridMesh && gridGeo && basePositions) {
        // Infinite Z flight animation
        gridMesh.position.z = (elapsedTime * 5.0) % 2.4;

        // Audio Frequency Waveform Vertex Displacement
        const posAttr = gridGeo.attributes.position;
        const array = posAttr.array;
        const vertexCount = posAttr.count;

        for (let i = 0; i < vertexCount; i++) {
          const x = basePositions[i * 3];
          const y = basePositions[i * 3 + 1];
          const distFromCenter = Math.abs(x);

          // Calculate liquid wave displacement based on x distance and time
          const freqFactor = frequencyData && frequencyData.length > 0 ? (frequencyData[i % 32] / 255.0) : 0.4;
          const waveHeight = Math.sin(y * 0.4 + elapsedTime * 4.0) * Math.cos(x * 0.3 + elapsedTime * 2.0) * (0.4 + freqFactor * 1.8 + beatPulse * 0.6);

          // Apply displacement to Z coordinate (which is vertical Y when rotated)
          array[i * 3 + 2] = basePositions[i * 3 + 2] + waveHeight * Math.min(1.0, distFromCenter * 0.1);
        }
        posAttr.needsUpdate = true;
      }

      if (sunMesh) {
        const sunScale = 1.0 + (beatPulse * 0.15);
        sunMesh.scale.set(sunScale, sunScale, 1.0);
      }
    }
  }
}
