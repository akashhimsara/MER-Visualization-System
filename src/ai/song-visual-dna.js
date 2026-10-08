import * as THREE from 'three';
import { VISUAL_MODES } from '../visuals/modes.js';

const MODE_FAMILIES = {
  CALM: [VISUAL_MODES.COSMIC_IRIS, VISUAL_MODES.PARTICLE_AURORA, VISUAL_MODES.COSMIC_BLOOM],
  HAPPY: [VISUAL_MODES.COSMIC_BLOOM, VISUAL_MODES.PARTICLE_AURORA, VISUAL_MODES.NEON_MANDALA],
  ENERGETIC: [VISUAL_MODES.NEON_MANDALA, VISUAL_MODES.PARTICLE_AURORA],
  SAD: [VISUAL_MODES.COSMIC_IRIS, VISUAL_MODES.COSMIC_BLOOM, VISUAL_MODES.PARTICLE_AURORA]
};

const PROFILE_MODE_FAMILIES = {
  PULSE_DRIVEN: [VISUAL_MODES.NEON_MANDALA, VISUAL_MODES.PARTICLE_AURORA],
  VOCAL_FORWARD: [VISUAL_MODES.PARTICLE_AURORA, VISUAL_MODES.COSMIC_BLOOM, VISUAL_MODES.COSMIC_IRIS],
  SOFT_ACOUSTIC: [VISUAL_MODES.COSMIC_BLOOM, VISUAL_MODES.COSMIC_IRIS, VISUAL_MODES.PARTICLE_AURORA],
  AIRY_AMBIENT: [VISUAL_MODES.COSMIC_IRIS, VISUAL_MODES.PARTICLE_AURORA, VISUAL_MODES.COSMIC_BLOOM],
  BALANCED: null,
  ANALYZING: null
};

function hashText(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index++) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function randomFromSeed(seed) {
  let state = seed >>> 0;
  return () => {
    state += 0x6D2B79F5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Stable song identity. It deliberately uses metadata only; no claim is made
 * that this is an audio embedding or an MER feature.
 */
export function fingerprintSong(file) {
  const descriptor = [file?.name || 'manual-demo', file?.size || 0, file?.lastModified || 0, file?.type || 'audio/unknown'].join('|');
  return { descriptor, seed: hashText(descriptor) };
}

/**
 * Builds a deterministic visual recipe. Same song + same emotion = same
 * recipe; a different song can select a different compatible visual family.
 */
export function createSongVisualDNA(songFingerprint, emotionCategory, baseColor, audioProfile = { key: 'ANALYZING' }, lockedVisualMode = null) {
  const category = MODE_FAMILIES[emotionCategory] ? emotionCategory : 'CALM';
  const profileKey = PROFILE_MODE_FAMILIES[audioProfile?.key] ? audioProfile.key : 'ANALYZING';
  const seed = hashText(`${songFingerprint.descriptor}|${category}|${profileKey}`);
  const random = randomFromSeed(seed);
  const families = PROFILE_MODE_FAMILIES[profileKey] || MODE_FAMILIES[category];
  const visualMode = lockedVisualMode || families[Math.floor(random() * families.length)];

  const primaryColor = new THREE.Color(baseColor ?? 0x35f6ff);
  primaryColor.offsetHSL((random() - 0.5) * 0.16, (random() - 0.5) * 0.10, (random() - 0.5) * 0.08);
  const secondaryColor = primaryColor.clone().offsetHSL(0.34 + random() * 0.18, 0.06, 0.04);

  return {
    version: 'song-visual-dna-v2',
    songFingerprint,
    seed,
    emotionCategory: category,
    audioProfile: { key: profileKey, confidence: audioProfile?.confidence || 0 },
    visualMode,
    isFamilyLocked: Boolean(lockedVisualMode),
    palette: { primary: primaryColor.getHex(), secondary: secondaryColor.getHex() },
    variation: {
      cameraRadius: Number((8.0 + random() * 2.6).toFixed(2)),
      cameraOrbitSpeed: Number((0.045 + random() * 0.085).toFixed(3)),
      visualEnergy: Number((0.78 + random() * 0.48).toFixed(2)),
      ribbonDensity: 0.7 + random() * 0.3
    }
  };
}
