import { applyVisualParameters } from './parameters.js';

/**
 * Canonical manual-input presets for the Member 2 standalone demo.
 *
 * These are inputs to the emotion-to-visual mapping pipeline, not outputs
 * from a Music Emotion Recognition (MER) model. Live MER integration is
 * intentionally outside the 50% standalone milestone.
 */
export const EMOTION_VA_PRESETS = Object.freeze({
  CALM: Object.freeze({ valence: 0.60, arousal: -0.50 }),
  HAPPY: Object.freeze({ valence: 0.70, arousal: 0.40 }),
  ENERGETIC: Object.freeze({ valence: 0.80, arousal: 0.90 }),
  SAD: Object.freeze({ valence: -0.70, arousal: -0.60 })
});

/**
 * High-contrast Emotion-to-Visual-Parameter Preset Mappings.
 */
export const EMOTION_PRESETS = {
  CALM: {
    particleColor: 0x00d4ff,   // Serene Sky Blue / Neon Cyan
    particleSize: 0.18,
    particleOpacity: 0.65,
    motionSpeed: 0.4,          // Smooth floating drift
    motionIntensity: 0.3,
    lightColor: 0x0088ff,
    lightIntensity: 2.2,
    bgTint: 0x02050e           // Deep midnight pitch space
  },
  HAPPY: {
    particleColor: 0xffaa00,   // Sun Gold Yellow
    particleSize: 0.22,
    particleOpacity: 0.85,
    motionSpeed: 1.2,          // Upbeat bounce
    motionIntensity: 1.0,
    lightColor: 0xffaa00,
    lightIntensity: 3.2,
    bgTint: 0x0c0702           // Warm dark amber background
  },
  ENERGETIC: {
    particleColor: 0xff0077,   // Electric Laser Pink / Magenta
    particleSize: 0.26,
    particleOpacity: 0.95,
    motionSpeed: 2.4,          // Fast EDM pulse
    motionIntensity: 2.2,
    lightColor: 0xff00aa,
    lightIntensity: 4.5,
    bgTint: 0x0e020a           // Dark magenta background
  },
  SAD: {
    particleColor: 0x4a6572,   // Gloomy Rain Steel Blue
    particleSize: 0.14,
    particleOpacity: 0.4,
    motionSpeed: 0.2,          // Slow heavy drift
    motionIntensity: 0.15,
    lightColor: 0x263238,
    lightIntensity: 0.8,
    bgTint: 0x010204           // Pitch dark gloom space
  }
};

/**
 * Applies emotion preset parameters directly to the engine targets.
 * 
 * @param {object} engineState - Container with { scene, placeholderMesh, particles, lighting }
 * @param {string} emotionName - 'CALM' | 'HAPPY' | 'ENERGETIC' | 'SAD'
 * @returns {object} The applied visual parameter bundle
 */
export function setEmotionState(engineState, emotionName) {
  const normalizedKey = String(emotionName).toUpperCase();
  const preset = EMOTION_PRESETS[normalizedKey] || EMOTION_PRESETS.CALM;

  applyVisualParameters(engineState, preset);
  return preset;
}
