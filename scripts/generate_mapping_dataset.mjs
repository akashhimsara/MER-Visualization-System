import { writeFile } from 'node:fs/promises';

const OUTPUT_PATH = new URL('../src/ai/mapping_dataset_v1.json', import.meta.url);
const GRID = [-0.95, -0.75, -0.55, -0.35, -0.15, 0.15, 0.35, 0.55, 0.75, 0.95];

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const round = (value, decimals = 3) => Number(value.toFixed(decimals));

function categoryFor(valence, arousal) {
  if (arousal < 0 && valence < 0) return 'SAD';
  if (arousal < 0) return 'CALM';
  if (valence < 0 || arousal > 0.5) return 'ENERGETIC';
  return 'HAPPY';
}

function visualModeFor(category) {
  return {
    CALM: 'HOLOGRAPHIC_CORE',
    HAPPY: 'EQUALIZER_RING',
    ENERGETIC: 'NEON_TUNNEL',
    SAD: 'HORIZON_GRID'
  }[category];
}

function hueFor(category, valence, arousal) {
  const v = (valence + 1) / 2;
  const a = (arousal + 1) / 2;
  if (category === 'CALM') return 0.48 + v * 0.07;
  if (category === 'HAPPY') return 0.10 + a * 0.16;
  if (category === 'SAD') return 0.57 + v * 0.03;
  return valence < 0 ? 0.62 + a * 0.14 : 0.76 + a * 0.17;
}

function createRecord(recordId, valence, arousal) {
  const normValence = (valence + 1) / 2;
  const normArousal = (arousal + 1) / 2;
  const emotionCategory = categoryFor(valence, arousal);
  const highEnergy = normArousal;

  return {
    recordId,
    datasetVersion: 'mapping-v1',
    recordSource: 'researcher_created_controlled_baseline',
    valence,
    arousal,
    emotionCategory,
    visualMode: visualModeFor(emotionCategory),
    hue: round(hueFor(emotionCategory, valence, arousal)),
    saturation: round(emotionCategory === 'SAD' ? 0.20 + normValence * 0.22 : 0.72 + highEnergy * 0.23),
    brightness: round(clamp(0.24 + normValence * 0.20 + highEnergy * 0.18, 0.20, 0.65)),
    particleDensity: Math.round(150 + highEnergy * 330),
    particleSize: round(0.13 + highEnergy * 0.23),
    particleSpeed: round(0.20 + highEnergy * 2.20),
    motionIntensity: round(0.15 + highEnergy * 2.05),
    lightIntensity: round(0.75 + normValence * 0.95 + highEnergy * 2.35),
    bloomStrength: round(0.22 + highEnergy * 0.45)
  };
}

const records = [];
let recordId = 1;
for (const valence of GRID) {
  for (const arousal of GRID) {
    records.push(createRecord(recordId++, valence, arousal));
  }
}

await writeFile(OUTPUT_PATH, `${JSON.stringify(records, null, 2)}\n`, 'utf8');
console.log(`Wrote ${records.length} deterministic mapping records to ${OUTPUT_PATH.pathname}`);
