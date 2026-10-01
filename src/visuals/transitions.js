import * as THREE from 'three';
import { EMOTION_PRESETS } from './emotions.js';
import { applyVisualParameters } from './parameters.js';

/**
 * Creates and initializes a Transition Controller object.
 * @returns {object} Transition state container
 */
export function createTransitionController() {
  const initialColor = new THREE.Color(0x00e1ff);
  const initialLightColor = new THREE.Color(0x0088ff);

  return {
    isTransitioning: false,
    duration: 1.5, // Default transition duration in seconds
    elapsed: 0.0,
    startParams: {
      particleColor: initialColor.clone(),
      particleSize: 0.14,
      particleOpacity: 0.75,
      motionSpeed: 0.4,
      motionIntensity: 0.3,
      lightColor: initialLightColor.clone(),
      lightIntensity: 0.8,
      bgTint: new THREE.Color(0x020a14)
    },
    targetParams: {
      particleColor: initialColor.clone(),
      particleSize: 0.14,
      particleOpacity: 0.75,
      motionSpeed: 0.4,
      motionIntensity: 0.3,
      lightColor: initialLightColor.clone(),
      lightIntensity: 0.8,
      bgTint: new THREE.Color(0x020a14)
    },
    currentParams: {
      particleColor: initialColor.clone(),
      particleSize: 0.14,
      particleOpacity: 0.75,
      motionSpeed: 0.4,
      motionIntensity: 0.3,
      lightColor: initialLightColor.clone(),
      lightIntensity: 0.8,
      bgTint: new THREE.Color(0x020a14)
    }
  };
}

/**
 * Starts a smooth transition towards a target emotion preset over a specified duration.
 * 
 * @param {object} controller - Transition controller instance
 * @param {string|object} targetEmotion - Emotion key ('HAPPY', 'ENERGETIC', etc.) or parameter bundle
 * @param {number} durationSeconds - Transition duration in seconds (default: 1.5s)
 */
export function startEmotionTransition(controller, targetEmotion, durationSeconds = 1.5) {
  if (!controller) return;

  const targetPreset = typeof targetEmotion === 'string'
    ? (EMOTION_PRESETS[String(targetEmotion).toUpperCase()] || EMOTION_PRESETS.CALM)
    : targetEmotion;

  // Snapshot current state as starting point
  controller.startParams.particleColor.copy(controller.currentParams.particleColor);
  controller.startParams.particleSize = controller.currentParams.particleSize || 0.14;
  controller.startParams.particleOpacity = controller.currentParams.particleOpacity || 0.85;
  controller.startParams.motionSpeed = controller.currentParams.motionSpeed;
  controller.startParams.motionIntensity = controller.currentParams.motionIntensity;
  controller.startParams.lightColor.copy(controller.currentParams.lightColor);
  controller.startParams.lightIntensity = controller.currentParams.lightIntensity;
  controller.startParams.bgTint.copy(controller.currentParams.bgTint);

  // Set target state
  controller.targetParams.particleColor.set(targetPreset.particleColor);
  controller.targetParams.particleSize = targetPreset.particleSize !== undefined ? targetPreset.particleSize : 0.14;
  controller.targetParams.particleOpacity = targetPreset.particleOpacity !== undefined ? targetPreset.particleOpacity : 0.85;
  controller.targetParams.motionSpeed = targetPreset.motionSpeed;
  controller.targetParams.motionIntensity = targetPreset.motionIntensity;
  controller.targetParams.lightColor.set(targetPreset.lightColor);
  controller.targetParams.lightIntensity = targetPreset.lightIntensity;
  controller.targetParams.bgTint.set(targetPreset.bgTint || 0x050508);

  controller.duration = Math.max(0.1, durationSeconds);
  controller.elapsed = 0.0;
  controller.isTransitioning = true;
}

/**
 * Updates the smooth transition interpolation on every frame.
 * 
 * @param {object} controller - Transition controller instance
 * @param {object} engineState - Container with { scene, particles, lighting }
 * @param {number} deltaTime - Time step in seconds
 */
export function updateEmotionTransition(controller, engineState, deltaTime = 0.016) {
  if (!controller || !engineState) return;

  if (controller.isTransitioning) {
    controller.elapsed += deltaTime;
    const progress = Math.min(1.0, controller.elapsed / controller.duration);

    // Smooth easeInOutCubic easing curve for organic transitions
    const easeProgress = progress < 0.5
      ? 4 * progress * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 3) / 2;

    // Interpolate Color values
    controller.currentParams.particleColor.copy(controller.startParams.particleColor).lerp(controller.targetParams.particleColor, easeProgress);
    controller.currentParams.lightColor.copy(controller.startParams.lightColor).lerp(controller.targetParams.lightColor, easeProgress);
    controller.currentParams.bgTint.copy(controller.startParams.bgTint).lerp(controller.targetParams.bgTint, easeProgress);

    // Interpolate Scalars
    controller.currentParams.particleSize = THREE.MathUtils.lerp(controller.startParams.particleSize, controller.targetParams.particleSize, easeProgress);
    controller.currentParams.particleOpacity = THREE.MathUtils.lerp(controller.startParams.particleOpacity, controller.targetParams.particleOpacity, easeProgress);
    controller.currentParams.motionSpeed = THREE.MathUtils.lerp(controller.startParams.motionSpeed, controller.targetParams.motionSpeed, easeProgress);
    controller.currentParams.motionIntensity = THREE.MathUtils.lerp(controller.startParams.motionIntensity, controller.targetParams.motionIntensity, easeProgress);
    controller.currentParams.lightIntensity = THREE.MathUtils.lerp(controller.startParams.lightIntensity, controller.targetParams.lightIntensity, easeProgress);

    if (progress >= 1.0) {
      controller.isTransitioning = false;
    }
  }

  // ALWAYS apply current parameters to engine state on every frame!
  applyVisualParameters(engineState, controller.currentParams, false);
}
