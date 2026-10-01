import * as THREE from 'three';

/**
 * Russell's Circumplex Model of Emotion: Valence-Arousal AI Visual Mapping Schema.
 * 
 * Maps continuous Emotion Coordinates (Valence, Arousal) in range [-1.0, +1.0]
 * to continuous 3D Visual Parameters (Color, Particle Size, Motion Speed, Lighting).
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
    // High A, High V -> Gold/Yellow to Laser Magenta/Pink
    // High A, Low V  -> Crimson Red / Intense Orange
    // Low A, Low V   -> Gloomy Slate Blue / Grey
    // Low A, High V  -> Serene Cyan / Ocean Blue
    let hue = 0.5; // Default Cyan
    let saturation = 0.8;
    let lightness = 0.5;

    if (v >= 0 && a >= 0) {
      // Quadrant 1: High V, High A (HAPPY / ENERGETIC) -> Yellow (0.13) to Pink (0.92)
      hue = THREE.MathUtils.lerp(0.13, 0.92, normA);
      saturation = 0.95;
      lightness = 0.55;
    } else if (v < 0 && a >= 0) {
      // Quadrant 2: Low V, High A (ANGRY / INTENSE) -> Deep Red (0.0) to Purple (0.8)
      hue = THREE.MathUtils.lerp(0.0, 0.78, normA);
      saturation = 0.9;
      lightness = 0.45;
    } else if (v < 0 && a < 0) {
      // Quadrant 3: Low V, Low A (SAD / DEPRESSED) -> Slate Blue / Grey (0.58)
      hue = 0.58;
      saturation = THREE.MathUtils.lerp(0.15, 0.4, normV);
      lightness = THREE.MathUtils.lerp(0.2, 0.4, normA);
    } else {
      // Quadrant 4: High V, Low A (CALM / RELAXED) -> Sky Blue / Turquoise (0.52)
      hue = THREE.MathUtils.lerp(0.48, 0.55, normV);
      saturation = 0.85;
      lightness = 0.5;
    }

    const colorObj = new THREE.Color().setHSL(hue, saturation, lightness);
    const hexColor = colorObj.getHex();

    // 2. Particle Size: Primary driver is Arousal (Range: 0.20 to 0.90)
    const particleSize = THREE.MathUtils.lerp(0.20, 0.90, normA);

    // 3. Particle Opacity: Range [0.4 to 1.0]
    const particleOpacity = THREE.MathUtils.lerp(0.4, 1.0, (normV + normA) / 2.0);

    // 4. Motion Speed: Driven strongly by Arousal (Range: 0.15 to 2.8)
    const motionSpeed = THREE.MathUtils.lerp(0.15, 2.8, normA);

    // 5. Motion Intensity (Turbulence): Driven by Arousal & Valence (Range: 0.1 to 2.8)
    const motionIntensity = THREE.MathUtils.lerp(0.1, 2.8, normA);

    // 6. Light Intensity: Driven by both V and A (Range: 0.4 to 4.0)
    const lightIntensity = THREE.MathUtils.lerp(0.4, 4.0, (normV * 0.3 + normA * 0.7));

    // 7. Background Tint: Dynamic dark hue matching primary color accent
    const bgObj = new THREE.Color().setHSL(hue, saturation * 0.5, 0.04 + normA * 0.04);
    const bgTint = bgObj.getHex();

    return {
      valence: v,
      arousal: a,
      particleColor: hexColor,
      particleSize,
      particleOpacity,
      motionSpeed,
      motionIntensity,
      lightColor: hexColor,
      lightIntensity,
      bgTint
    };
  }
}
