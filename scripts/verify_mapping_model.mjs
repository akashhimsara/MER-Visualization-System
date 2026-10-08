import dataset from '../src/ai/mapping_dataset_v1.json' with { type: 'json' };
import { EmotionAIModel } from '../src/ai/emotion-ai-model.js';
import { EMOTION_VA_PRESETS } from '../src/visuals/emotions.js';

const model = new EmotionAIModel();
const evaluation = model.evaluate();

if (!model.isTrained) {
  throw new Error('Model weights are missing. Run the training pipeline before the viva demo.');
}

if (dataset.length !== evaluation.trainingRecordCount + evaluation.heldOutTestRecordCount) {
  throw new Error('Dataset and training split counts do not match the exported model metadata.');
}

console.log('Member 2 mapping-model evidence');
console.log(`Dataset: ${dataset.length} controlled mapping records (${evaluation.datasetVersion})`);
console.log(`Model: ${evaluation.modelName}`);
console.log(`Split: ${evaluation.trainingRecordCount} training / ${evaluation.heldOutTestRecordCount} held-out test records`);
console.log('Live browser inference samples:');

for (const [emotion, va] of Object.entries(EMOTION_VA_PRESETS)) {
  const prediction = model.predict(va.valence, va.arousal);
  const colour = `#${prediction.particleColor.toString(16).padStart(6, '0').toUpperCase()}`;
  console.log(
    `  ${emotion}: ${prediction.predictedCategory}, ${prediction.particleDensity} particles, ` +
    `speed ${prediction.motionSpeed.toFixed(2)}, bloom ${prediction.bloomStrength.toFixed(2)}, ${colour}`
  );
}

console.log('Verification passed: dataset -> exported weights -> browser prediction pipeline is available.');
