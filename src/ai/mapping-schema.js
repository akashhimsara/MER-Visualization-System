import * as THREE from 'three';

/**
 * Verified Literature Citations grounding the Emotion-to-Visual Parameter Mappings:
 * 
 * [1] Dharmapriya et al. (2021) - "Music emotion visualization through colour" (Valence/Arousal -> Hue/Saturation)
 * [2] Fonteles et al. (2013) - "Creating and evaluating a particle system for music visualization" (Energy -> Particle Velocity & Density)
 * [3] Hsiao et al. (2017) - "Methodology for stage lighting control based on music emotions" (Arousal -> Lighting Intensity)
 * [4] Kurilcik et al. (2024) - "Analyzing the relationship between sound, color, and emotion" (Audio Frequency -> Visual Texture)
 */
export const RESEARCH_CITATIONS = [
  { id: 'Dharmapriya2021', title: 'Music emotion visualization through colour', doi: '10.1109/ICEIC51217.2021.9369788' },
  { id: 'Fonteles2013', title: 'Creating and evaluating a particle system for music visualization', doi: '10.1016/j.jvlc.2013.10.002' },
  { id: 'Hsiao2017', title: 'Methodology for stage lighting control based on music emotions', doi: '10.1016/j.ins.2017.05.002' },
  { id: 'Kurilcik2024', title: 'Analyzing the relationship between sound, color, and emotion', doi: '10.1016/j.procs.2024.09.226' }
];

/**
 * Master Schema Definition for Emotion-to-Visual Parameters Mapping Records.
 */
export const MAPPING_DATASET_SCHEMA = {
  features: ['valence', 'arousal', 'emotion_category'],
  targets: [
    'hue',
    'saturation',
    'brightness',
    'particle_density',
    'particle_size',
    'particle_speed',
    'motion_intensity',
    'lighting_intensity',
    'bloom_strength',
    'hex_color',
    'bg_tint'
  ]
};

/**
 * Russell's Circumplex Model of Emotion: Valence-Arousal AI Visual Mapping Schema.
 * Maps continuous Emotion Coordinates (Valence, Arousal) in range [-1.0, +1.0]
 * to continuous 3D Visual Parameters (Color, Particles, Motion, Lighting, Bloom).
 */
export class EmotionVisualMapper {
  /**
   * Maps continuous Valence (-1.0 to 1.0) and Arousal (-1.0 to 1.0)
   * to a continuous target Visual Parameter bundle.
   * 
   * @param {number} valence - Positivity/Pleasure (-1.0 = Sad/Negative, +1.0 = Happy/Positive)
   * @param {number} arousal - Activation/Energy (-1.0 = Calm/Passive, +1.0 = Energetic/Active)
   * @returns {object} Visual parameter targets bundle
   */
  static mapValenceArousalToVisuals(valence = 0.0, arousal = 0.0) {
    // Clamp inputs to [-1.0, 1.0]
    const v = Math.min(1.0, Math.max(-1.0, valence));
    const a = Math.min(1.0, Math.max(-1.0, arousal));

    // Normalize v and a to range [0.0, 1.0]
    const normV = (v + 1.0) / 2.0;
    const normA = (a + 1.0) / 2.0;

    // 1. Color HSL Calculation based on Circumplex Quadrants
    let hue = 0.52; // Default Cyan
    let saturation = 0.85;
    let lightness = 0.50;
    let emotionCategory = 'CALM';

    if (v >= 0 && a >= 0) {
      // Quadrant 1: High V, High A (HAPPY / ENERGETIC) -> Yellow (0.13) to Pink (0.92)
      hue = THREE.MathUtils.lerp(0.13, 0.92, normA);
      saturation = 0.95;
      lightness = 0.55;
      emotionCategory = a > 0.5 ? 'ENERGETIC' : 'HAPPY';
    } else if (v < 0 && a >= 0) {
      // Quadrant 2: Low V, High A (ANGRY / INTENSE) -> Deep Red (0.0) to Purple (0.78)
      hue = THREE.MathUtils.lerp(0.0, 0.78, normA);
      saturation = 0.90;
      lightness = 0.45;
      emotionCategory = 'ENERGETIC';
    } else if (v < 0 && a < 0) {
      // Quadrant 3: Low V, Low A (SAD / DEPRESSED) -> Gloomy Steel Blue (0.58)
      hue = 0.58;
      saturation = THREE.MathUtils.lerp(0.20, 0.45, normV);
      lightness = THREE.MathUtils.lerp(0.25, 0.40, normA);
      emotionCategory = 'SAD';
    } else {
      // Quadrant 4: High V, Low A (CALM / RELAXED) -> Sky Blue / Turquoise (0.52)
      hue = THREE.MathUtils.lerp(0.48, 0.55, normV);
      saturation = 0.85;
      lightness = 0.50;
      emotionCategory = 'CALM';
    }

    let entityForm = 'ASTRAL_HOLOGRAM_ENTITY';
    if (emotionCategory === 'ENERGETIC') {
      entityForm = 'CYBER_KINETIC_HUMANOID';
    } else if (emotionCategory === 'HAPPY') {
      entityForm = 'EUPHORIC_DANCER_AVATAR';
    } else if (emotionCategory === 'SAD') {
      entityForm = 'GHOST_WIREFRAME_SPIRIT';
    } else {
      entityForm = 'ASTRAL_HOLOGRAM_ENTITY';
    }

    const colorObj = new THREE.Color().setHSL(hue, saturation, lightness);
    const hexColor = colorObj.getHex();

    // 2. Particle Size & Density: Driven by Arousal & Valence
    const particleDensity = Math.round(THREE.MathUtils.lerp(150, 450, normA));
    const particleSize = THREE.MathUtils.lerp(0.14, 0.35, normA);
    const particleOpacity = THREE.MathUtils.lerp(0.5, 0.95, (normV + normA) / 2.0);

    // 3. Motion Speed & Turbulence: Driven by Arousal
    const motionSpeed = THREE.MathUtils.lerp(0.2, 2.4, normA);
    const motionIntensity = THREE.MathUtils.lerp(0.15, 2.2, normA);

    // 4. Studio Light Intensity & Bloom: Driven by Arousal & Valence
    const lightIntensity = THREE.MathUtils.lerp(0.8, 4.0, (normV * 0.3 + normA * 0.7));
    const bloomStrength = THREE.MathUtils.lerp(0.25, 0.65, normA);

    // 5. Pitch Dark Background Tint
    const bgObj = new THREE.Color().setHSL(hue, saturation * 0.4, 0.02 + normA * 0.03);
    const bgTint = bgObj.getHex();

    return {
      valence: v,
      arousal: a,
      emotionCategory,
      entityForm,
      hue,
      saturation,
      brightness: lightness,
      particleColor: hexColor,
      particleDensity,
      particleSize,
      particleOpacity,
      particleSpeed: motionSpeed,
      motionSpeed,
      motionIntensity,
      lightColor: hexColor,
      lightIntensity,
      bloomStrength,
      bgTint
    };
  }

  /**
   * Generates a research-grounded synthetic dataset matrix for training the AI Mapping Model.
   * 
   * @param {number} samplesPerQuadrant - Number of samples per quadrant (default: 50 -> total 200)
   * @returns {Array<object>} Array of mapping data records
   */
  static generateDatasetRecords(samplesPerQuadrant = 50) {
    const records = [];

    const ranges = [
      { vMin: 0.0, vMax: 1.0, aMin: 0.0, aMax: 1.0 },   // Q1: Happy/Energetic
      { vMin: -1.0, vMax: 0.0, aMin: 0.0, aMax: 1.0 },  // Q2: Angry/Intense
      { vMin: -1.0, vMax: 0.0, aMin: -1.0, aMax: 0.0 }, // Q3: Sad
      { vMin: 0.0, vMax: 1.0, aMin: -1.0, aMax: 0.0 }   // Q4: Calm
    ];

    ranges.forEach(r => {
      for (let i = 0; i < samplesPerQuadrant; i++) {
        const v = r.vMin + Math.random() * (r.vMax - r.vMin);
        const a = r.aMin + Math.random() * (r.aMax - r.aMin);
        const mappedParams = EmotionVisualMapper.mapValenceArousalToVisuals(v, a);
        records.push(mappedParams);
      }
    });

    return records;
  }
}

