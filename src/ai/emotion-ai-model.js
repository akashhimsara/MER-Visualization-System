import * as THREE from 'three';
import modelWeights from './model_weights_v1.json' with { type: 'json' };
import { EmotionVisualMapper } from './mapping-schema.js';

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const VISUAL_MODE_BY_CATEGORY = {
  CALM: 'HOLOGRAPHIC_CORE',
  HAPPY: 'EQUALIZER_RING',
  ENERGETIC: 'NEON_TUNNEL',
  SAD: 'HORIZON_GRID'
};

/**
 * Browser-side inference wrapper for the versioned multi-output regression
 * model. Training is performed reproducibly by `npm run train:mapping-model`;
 * this class only loads saved weights and predicts renderer parameters.
 */
export class EmotionAIModel {
  constructor() {
    this.model = modelWeights;
    this.isTrained = Boolean(modelWeights?.weights);
    this.modelName = modelWeights.modelVersion;
    this.featureNames = modelWeights.featureNames;
    this.targetNames = modelWeights.targetNames;
  }

  featureVector(valence, arousal) {
    return [1, valence, arousal, valence * valence, valence * arousal, arousal * arousal];
  }

  predictTarget(targetName, vector) {
    const weights = this.model.weights[targetName];
    return weights.reduce((total, weight, index) => total + weight * vector[index], 0);
  }

  /**
   * Predicts the visual parameter vector from continuous VA coordinates.
   * Inputs are clamped to the documented range before inference.
   */
  predict(valence = 0.0, arousal = 0.0) {
    const v = clamp(valence, -1.0, 1.0);
    const a = clamp(arousal, -1.0, 1.0);
    const vector = this.featureVector(v, a);
    const target = Object.fromEntries(
      this.targetNames.map(name => [name, this.predictTarget(name, vector)])
    );
    const emotionContext = EmotionVisualMapper.mapValenceArousalToVisuals(v, a);

    const hue = clamp(target.hue, 0, 1);
    const saturation = clamp(target.saturation, 0, 1);
    const brightness = clamp(target.brightness, 0, 1);
    const particleColor = new THREE.Color().setHSL(hue, saturation, brightness).getHex();
    const normValence = (v + 1) / 2;
    const normArousal = (a + 1) / 2;
    const backgroundColor = new THREE.Color().setHSL(hue, saturation * 0.35, 0.018 + normArousal * 0.032).getHex();

    return {
      valence: v,
      arousal: a,
      predictedCategory: emotionContext.emotionCategory,
      visualMode: VISUAL_MODE_BY_CATEGORY[emotionContext.emotionCategory],
      hue,
      saturation,
      brightness,
      particleColor,
      particleDensity: Math.round(clamp(target.particleDensity, 100, 1000)),
      particleSize: clamp(target.particleSize, 0.10, 1.00),
      particleOpacity: clamp(0.48 + ((normValence + normArousal) / 2) * 0.47, 0.40, 0.95),
      particleSpeed: clamp(target.particleSpeed, 0.10, 3.00),
      motionSpeed: clamp(target.particleSpeed, 0.10, 3.00),
      motionIntensity: clamp(target.motionIntensity, 0.10, 3.00),
      lightColor: particleColor,
      lightIntensity: clamp(target.lightIntensity, 0.20, 5.00),
      bloomStrength: clamp(target.bloomStrength, 0.15, 0.80),
      bgTint: backgroundColor
    };
  }

  /**
   * Returns the fixed held-out evaluation created during training. These
   * scores concern the controlled mapping dataset only, not listener study
   * performance or music-emotion-recognition accuracy.
   */
  evaluate() {
    return {
      modelName: this.modelName,
      datasetVersion: this.model.datasetVersion,
      trainingRecordCount: this.model.training.recordCount,
      heldOutTestRecordCount: this.model.evaluation.recordCount,
      metrics: this.model.evaluation.metrics,
      isTrained: this.isTrained
    };
  }
}
