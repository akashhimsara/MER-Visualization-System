import * as THREE from 'three';

const RIBBON_POINTS = 150;

function createRibbon(color, opacity) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(RIBBON_POINTS * 3), 3));
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false });
  return new THREE.Line(geometry, material);
}

/** Full-frame animated neon current field, designed for high-energy cosmic music. */
export function createParticleAurora() {
  const group = new THREE.Group();
  group.name = 'mode_particleAurora';
  group.position.y = 1.35;
  const primary = new THREE.Color(0x26f6e9);
  const secondary = new THREE.Color(0xb45cff);
  const ribbons = [];

  for (let index = 0; index < 32; index++) {
    const ribbon = createRibbon(index % 2 ? secondary : primary, 0.28 + (index % 5) * 0.07);
    ribbon.position.z = -0.8 - index * 0.025;
    group.add(ribbon);
    ribbons.push({ ribbon, material: ribbon.material, index, band: Math.floor(index / 8) });
  }

  const particleCount = 1800;
  const positions = new Float32Array(particleCount * 3);
  const base = new Float32Array(particleCount * 3);
  for (let index = 0; index < particleCount; index++) {
    const x = (Math.random() - 0.5) * 18;
    const y = (Math.random() - 0.5) * 10;
    const z = -1.8 - Math.random() * 2;
    positions[index * 3] = base[index * 3] = x;
    positions[index * 3 + 1] = base[index * 3 + 1] = y;
    positions[index * 3 + 2] = base[index * 3 + 2] = z;
  }
  const particleGeometry = new THREE.BufferGeometry();
  particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const particleMaterial = new THREE.PointsMaterial({ color: primary, size: 0.033, transparent: true, opacity: 0.82, blending: THREE.AdditiveBlending, depthWrite: false });
  const particles = new THREE.Points(particleGeometry, particleMaterial);
  group.add(particles);

  const core = new THREE.Mesh(new THREE.RingGeometry(0.40, 0.46, 64), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.86, blending: THREE.AdditiveBlending }));
  group.add(core);
  group.userData = { ribbons, particles, particleMaterial, base, core, primary, secondary };
  return group;
}

export function updateParticleAurora(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { ribbons, particles, base, core } = group.userData;
  let highEnergy = 0.18;
  let bassEnergy = beatPulse;
  if (frequencyData?.length) {
    const highStart = Math.floor(frequencyData.length * 0.54);
    let highSum = 0;
    let bassSum = 0;
    for (let index = 0; index < highStart; index++) bassSum += frequencyData[index];
    for (let index = highStart; index < frequencyData.length; index++) highSum += frequencyData[index];
    bassEnergy = Math.max(beatPulse, bassSum / Math.max(1, highStart * 255));
    highEnergy = highSum / Math.max(1, (frequencyData.length - highStart) * 255);
  }
  ribbons.forEach(({ ribbon, index, band }) => {
    const positions = ribbon.geometry.attributes.position.array;
    const phase = elapsedTime * (0.65 + band * 0.12) + index * 0.48;
    const baseY = (band - 1.5) * 1.42 + ((index % 8) - 3.5) * 0.10;
    for (let point = 0; point < RIBBON_POINTS; point++) {
      const t = point / (RIBBON_POINTS - 1);
      const x = (t - 0.5) * 18;
      const wave = Math.sin(t * 11 + phase) * (0.38 + highEnergy * 0.82) + Math.sin(t * 4 - phase * 0.73) * 0.32;
      positions[point * 3] = x;
      positions[point * 3 + 1] = baseY + wave + Math.sin(t * 18 + phase) * 0.10;
      positions[point * 3 + 2] = -0.8 - band * 0.28 + Math.cos(t * 8 + phase) * 0.15;
    }
    ribbon.geometry.attributes.position.needsUpdate = true;
    ribbon.material.opacity = 0.20 + highEnergy * 0.34 + beatPulse * 0.24;
  });
  const positions = particles.geometry.attributes.position.array;
  for (let index = 0; index < particles.geometry.attributes.position.count; index++) {
    const phase = elapsedTime * 0.85 + index * 0.13;
    positions[index * 3] = base[index * 3] + Math.sin(phase) * (0.10 + highEnergy * 0.28);
    positions[index * 3 + 1] = base[index * 3 + 1] + Math.cos(phase * 0.82) * (0.08 + highEnergy * 0.25);
  }
  particles.geometry.attributes.position.needsUpdate = true;
  particles.scale.setScalar(1 + bassEnergy * 0.10);
  core.scale.setScalar(1 + bassEnergy * 0.65);
  core.rotation.z += deltaTime * (0.6 + highEnergy * 1.8);
}

export function setParticleAuroraColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { ribbons, particleMaterial, core, primary, secondary } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.45, 0.04, 0.05));
  ribbons.forEach(({ material, index }) => material.color.copy(index % 2 ? secondary : primary));
  particleMaterial.color.copy(primary);
  core.material.color.copy(secondary);
}
