import * as THREE from 'three';

/**
 * Creates and initializes a Beat Reactivity Controller.
 * @returns {object} Beat controller instance
 */
export function createBeatController() {
  return {
    pulse: 0.0,              // Current beat pulse decay value (0.0 to 1.0)
    decayRate: 5.5,          // Exponential decay rate
    autoBeatEnabled: true,   // Auto 128 BPM EDM simulator for testing
    bpm: 128,
    lastBeatTime: 0
  };
}

/**
 * Triggers an immediate beat pulse (e.g. kick drum / bass drop hit).
 * 
 * @param {object} controller - Beat controller instance
 * @param {number} intensity - Pulse intensity scalar (0.0 to 1.0)
 */
export function triggerBeatPulse(controller, intensity = 1.0) {
  if (!controller) return;
  controller.pulse = Math.min(1.0, Math.max(0.0, intensity));
}

/**
 * Updates beat pulse decay and applies audio-reactive physical scales/flashes to Three.js elements.
 * 
 * @param {object} controller - Beat controller instance
 * @param {object} engineState - { scene, camera, spectrumRing, lighting, particles }
 * @param {number} elapsedTime - Total elapsed time in seconds
 * @param {number} deltaTime - Time step in seconds
 */
export function updateBeatReactor(controller, engineState, elapsedTime = 0, deltaTime = 0.016) {
  if (!controller || !engineState) return;

  // Auto 128 BPM EDM beat simulator (triggers a kick every ~0.468s)
  if (controller.autoBeatEnabled) {
    const beatInterval = 60.0 / controller.bpm;
    if (elapsedTime - controller.lastBeatTime >= beatInterval) {
      controller.lastBeatTime = elapsedTime;
      triggerBeatPulse(controller, 1.0);
    }
  }

  // Decay beat pulse value exponentially towards 0
  if (controller.pulse > 0.001) {
    controller.pulse = THREE.MathUtils.lerp(controller.pulse, 0.0, deltaTime * controller.decayRate);
  } else {
    controller.pulse = 0.0;
  }

  const pulse = controller.pulse;

  // 1. Central 3D Equalizer Ring Radial Pulse
  if (engineState.spectrumRing) {
    const targetScale = 1.0 + (pulse * 0.08);
    engineState.spectrumRing.scale.set(targetScale, 1.0, targetScale);
  }

  // 2. Central Point Light Intensity Boost on Beat Hit
  if (engineState.lighting) {
    if (engineState.lighting.pointLight) {
      const basePoint = engineState.lighting.basePointIntensity || 3.0;
      engineState.lighting.pointLight.intensity = basePoint + (pulse * 2.5);
    }

    if (engineState.lighting.ambientLight) {
      const baseAmbient = engineState.lighting.baseAmbientIntensity || 0.4;
      engineState.lighting.ambientLight.intensity = baseAmbient + (pulse * 0.25);
    }
  }

  // 3. Smooth Camera Micro FOV & Position Kick
  if (engineState.camera && engineState.camera.isPerspectiveCamera) {
    const baseFov = engineState.camera.userData?.baseFov || 55;
    const targetFov = baseFov - (pulse * 3.5);
    
    engineState.camera.fov = THREE.MathUtils.lerp(engineState.camera.fov, targetFov, deltaTime * 12.0);
    engineState.camera.updateProjectionMatrix();

    const targetCamY = 3.6 - (pulse * 0.3);
    engineState.camera.position.y = THREE.MathUtils.lerp(engineState.camera.position.y, targetCamY, deltaTime * 12.0);
  }

  // 4. Background Flare Glow Pulse
  if (engineState.bgFlareSprite) {
    const flareScale = 22.0 + (pulse * 6.0);
    engineState.bgFlareSprite.scale.set(flareScale, flareScale, 1);
    if (engineState.bgFlareSprite.material) {
      engineState.bgFlareSprite.material.opacity = 0.45 + (pulse * 0.3);
    }
  }
}


