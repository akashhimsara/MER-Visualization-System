import * as THREE from 'three';
import { setParticleColor, lerpParticleColor, setParticleStyle } from './color.js';
import { setMotionSpeed, setMotionIntensity } from './animation.js';
import { setLightColor, setLightIntensity } from './lighting.js';
import { setSpectrumColor } from './spectrum.js';
import { setAvatarEntityState } from './avatar.js';
import { setParticleDensity } from './particles.js';

/**
 * Default visual parameter configuration.
 */
export const DEFAULT_VISUAL_PARAMS = {
  particleColor: 0x00f3ff,
  particleSize: 0.45,
  particleOpacity: 0.9,
  motionSpeed: 1.0,
  motionIntensity: 1.0,
  lightColor: 0x00f3ff,
  lightIntensity: 1.5,
  bgTint: 0x050508
};

/**
 * Predefined visual parameter profiles for testing visual state changes.
 */
export const VISUAL_PROFILES = {
  CALM: {
    particleColor: 0x00e1ff,
    particleSize: 0.35,
    particleOpacity: 0.75,
    motionSpeed: 0.3,
    motionIntensity: 0.2,
    lightColor: 0x0088ff,
    lightIntensity: 0.8,
    bgTint: 0x020a14
  },
  HAPPY: {
    particleColor: 0xffd700,
    particleSize: 0.65,
    particleOpacity: 0.95,
    motionSpeed: 1.4,
    motionIntensity: 1.3,
    lightColor: 0xffaa00,
    lightIntensity: 2.5,
    bgTint: 0x140d02
  },
  ENERGETIC: {
    particleColor: 0xff0055,
    particleSize: 0.9,
    particleOpacity: 1.0,
    motionSpeed: 2.8,
    motionIntensity: 2.8,
    lightColor: 0xaa00ff,
    lightIntensity: 4.0,
    bgTint: 0x14020a
  },
  SAD: {
    particleColor: 0x4a6572,
    particleSize: 0.2,
    particleOpacity: 0.4,
    motionSpeed: 0.15,
    motionIntensity: 0.1,
    lightColor: 0x263238,
    lightIntensity: 0.4,
    bgTint: 0x030508
  }
};

/**
 * Applies a complete bundle of visual parameters (color, size, opacity, motion, lighting, background) to the visualization engine targets.
 * 
 * @param {object} engineState - Container with { scene, placeholderMesh, particles, lighting, modeManager }
 * @param {object} params - Visual parameters object
 */
export function applyVisualParameters(engineState, params = {}) {
  if (!engineState) return null;

  const { scene, placeholderMesh, particles, lighting, modeManager, bloomPass } = engineState;

  // 1. Direct Particle Color, Size, Opacity Update
  if (particles && particles.material) {
    if (params.particleColor !== undefined) {
      particles.material.color.set(params.particleColor);
    }
    if (params.particleSize !== undefined) {
      particles.material.size = params.particleSize;
      if (!particles.userData) particles.userData = {};
      particles.userData.baseSize = params.particleSize;
    }
    if (params.particleOpacity !== undefined) {
      particles.material.opacity = params.particleOpacity;
    }
    if (params.particleDensity !== undefined) {
      setParticleDensity(particles, params.particleDensity);
    }
    particles.material.needsUpdate = true;
  }

  // 2. Direct 3D Cyber Avatar Entity State & Color Update
  if (modeManager && modeManager.modes && modeManager.modes['CYBER_AVATAR']) {
    setAvatarEntityState(modeManager.modes['CYBER_AVATAR'], params.entityForm, params.particleColor);
  }

  // 2. Direct Cyber Core Color Update
  if (placeholderMesh && params.particleColor !== undefined) {
    placeholderMesh.children.forEach(child => {
      if (child.material) {
        child.material.color.set(params.particleColor);
        child.material.needsUpdate = true;
      }
    });
  }

  // 3. Direct 3D Spectrum Waveform Ring & Floor Ripples Color Update
  const { spectrumRing, floorRipples } = engineState;
  if (spectrumRing && params.particleColor !== undefined) {
    setSpectrumColor(spectrumRing, params.particleColor);
  }
  if (floorRipples && floorRipples.userData && floorRipples.userData.rings && params.particleColor !== undefined) {
    const rippleColor = new THREE.Color(params.particleColor);
    floorRipples.userData.rings.forEach(r => {
      if (r.mesh && r.mesh.material) {
        r.mesh.material.color.lerp(rippleColor, 0.25);
      }
    });
  }

  // 3. Direct Motion Speed & Intensity Update
  if (particles && particles.userData && particles.userData.motionConfig) {
    if (params.motionSpeed !== undefined) {
      particles.userData.motionConfig.speed = params.motionSpeed;
    }
    if (params.motionIntensity !== undefined) {
      particles.userData.motionConfig.intensity = params.motionIntensity;
    }
  }

  // 4. Direct Lighting Color & Intensity Update
  if (lighting) {
    if (lighting.pointLight) {
      if (params.lightColor !== undefined) {
        lighting.pointLight.color.set(params.lightColor);
      }
      if (params.lightIntensity !== undefined) {
        lighting.pointLight.intensity = params.lightIntensity;
        lighting.basePointIntensity = params.lightIntensity;
      }
    }
    if (lighting.ambientLight) {
      lighting.baseAmbientIntensity = Math.max(0.16, Math.min(0.75, (params.lightIntensity || lighting.basePointIntensity || 1.5) * 0.16));
      lighting.ambientLight.intensity = lighting.baseAmbientIntensity;
    }
  }

  // 5. Keep the world dark while allowing each emotion to tint its atmosphere.
  if (scene && params.bgTint !== undefined) {
    scene.background = new THREE.Color(params.bgTint);
  }

  // 6. Apply the predicted glow level to the post-processing bloom pass.
  if (bloomPass && params.bloomStrength !== undefined) {
    bloomPass.strength = params.bloomStrength;
  }

  return params;
}
