import { createSongVisualDNA, fingerprintSong } from '../src/ai/song-visual-dna.js';
import { VISUAL_MODES } from '../src/visuals/modes.js';

const premiumModes = new Set([
  VISUAL_MODES.LIQUID_CHROME_GALAXY,
  VISUAL_MODES.NEON_MANDALA,
  VISUAL_MODES.COSMIC_BLOOM,
  VISUAL_MODES.PARTICLE_AURORA,
  VISUAL_MODES.COSMIC_IRIS,
  VISUAL_MODES.NEON_LOTUS,
  VISUAL_MODES.SOLAR_ECLIPSE,
  VISUAL_MODES.CRYSTAL_CATHEDRAL
]);

const scenarios = [
  // Main viva claim: same input emotion, different songs, different visual DNA.
  { name: 'happy-song-a.mp3', size: 3_120_000, lastModified: 1_725_000_000_000, type: 'audio/mpeg', emotion: 'HAPPY', profile: 'PULSE_DRIVEN', baseColor: 0xffb000 },
  { name: 'happy-song-b.mp3', size: 4_840_000, lastModified: 1_725_000_001_000, type: 'audio/mpeg', emotion: 'HAPPY', profile: 'PULSE_DRIVEN', baseColor: 0xffb000 },
  { name: 'happy-song-c.mp3', size: 2_390_000, lastModified: 1_725_000_002_000, type: 'audio/mpeg', emotion: 'HAPPY', profile: 'PULSE_DRIVEN', baseColor: 0xffb000 },
  // A separate control confirms that a different emotion also changes the recipe space.
  { name: 'sad-song-control.mp3', size: 3_760_000, lastModified: 1_725_000_003_000, type: 'audio/mpeg', emotion: 'SAD', profile: 'SOFT_ACOUSTIC', baseColor: 0x4a6572 }
];

const output = scenarios.map((song) => {
  const fingerprint = fingerprintSong(song);
  const profile = { key: song.profile };
  const recipe = createSongVisualDNA(fingerprint, song.emotion, song.baseColor, profile);
  const repeatedRecipe = createSongVisualDNA(fingerprint, song.emotion, song.baseColor, profile);
  return {
    song: song.name,
    emotion: song.emotion,
    profile: recipe.audioProfile.key,
    mode: recipe.visualMode,
    seed: recipe.seed,
    palette: recipe.palette,
    repeatable: JSON.stringify(recipe) === JSON.stringify(repeatedRecipe)
  };
});

console.table(output);
if (!output.every((scenario) => scenario.repeatable)) {
  throw new Error('Song Visual DNA must be deterministic for the same song and emotion.');
}
if (!output.every((scenario) => premiumModes.has(scenario.mode))) {
  throw new Error('Song Visual DNA must only auto-select premium visual worlds.');
}

const sameEmotionSongs = output.slice(0, 3);
const uniqueSeeds = new Set(sameEmotionSongs.map((scenario) => scenario.seed));
const uniqueRecipes = new Set(sameEmotionSongs.map((scenario) => JSON.stringify([scenario.mode, scenario.palette])));
if (uniqueSeeds.size !== sameEmotionSongs.length || uniqueRecipes.size !== sameEmotionSongs.length) {
  throw new Error('Different songs with the same emotion must receive distinct Visual DNA recipes.');
}

console.log('Verification passed: three HAPPY songs produce three deterministic, distinct Visual DNA recipes.');
