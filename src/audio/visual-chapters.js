/** Stable music-energy chapters. These describe momentary intensity, not genre. */
export function createVisualChapterController() {
  return { key: 'DORMANT', energy: 0, average: 0.12, candidate: 'DORMANT', candidateAge: 0, changedAt: 0, surgeUntil: 0 };
}

export function updateVisualChapter(controller, metrics, elapsedTime, deltaTime) {
  if (!controller) return { key: 'DORMANT', intensity: 0 };
  const energy = metrics ? metrics.bass * 0.48 + metrics.mid * 0.34 + metrics.high * 0.18 : 0;
  controller.energy += (energy - controller.energy) * Math.min(1, deltaTime * 3.5);
  controller.average += (controller.energy - controller.average) * Math.min(1, deltaTime * 0.45);
  if (metrics?.isBeat && metrics.bass > 0.18) controller.surgeUntil = elapsedTime + 1.35;
  let next = 'FLOW';
  if (elapsedTime < controller.surgeUntil) next = 'SURGE';
  else if (controller.energy < 0.075) next = 'DORMANT';
  else if (controller.energy > controller.average * 1.15) next = 'BUILD';
  else if (controller.energy < controller.average * 0.72) next = 'RELEASE';
  if (next !== controller.candidate) { controller.candidate = next; controller.candidateAge = 0; }
  else controller.candidateAge += deltaTime;
  if (controller.candidate !== controller.key && (controller.candidate === 'SURGE' || controller.candidateAge > 0.55)) {
    controller.key = controller.candidate; controller.changedAt = elapsedTime;
  }
  return { key: controller.key, intensity: controller.energy, age: elapsedTime - controller.changedAt };
}
