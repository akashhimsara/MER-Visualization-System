import * as THREE from 'three';

const TAU = Math.PI * 2;

function crystalMaterial(color) {
  return new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.68, roughness: 0.08, metalness: 0.24, transparent: true, opacity: 0.66, side: THREE.DoubleSide });
}

/** Floating glass-like crystal architecture for vocal lifts and uplifting choruses. */
export function createCrystalCathedral() {
  const group = new THREE.Group();
  group.name = 'mode_crystalCathedral';
  group.position.y = 1.25;
  const primary = new THREE.Color(0x6cf6ff);
  const secondary = new THREE.Color(0xffb0e5);
  const towers = [];

  for (let index = 0; index < 17; index++) {
    const angle = (index / 17) * TAU + (index % 2) * 0.11;
    const radius = 1.15 + (index % 5) * 0.68;
    const height = 0.9 + (index % 6) * 0.36;
    const material = crystalMaterial(index % 2 ? primary : secondary);
    const tower = new THREE.Mesh(new THREE.ConeGeometry(0.14 + (index % 3) * 0.045, height, 6, 1), material);
    tower.position.set(Math.cos(angle) * radius, -0.9 + height * 0.5, Math.sin(angle) * radius * 0.18);
    tower.rotation.z = Math.cos(angle) * 0.16;
    group.add(tower);
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(tower.geometry), new THREE.LineBasicMaterial({ color: material.color, transparent: true, opacity: 0.82, blending: THREE.AdditiveBlending, depthWrite: false }));
    tower.add(edges);
    towers.push({ tower, material, edges, angle, radius, height, baseY: tower.position.y, phase: index * 0.73 });
  }

  const beams = [];
  for (let index = 0; index < 5; index++) {
    const beam = new THREE.Mesh(new THREE.ConeGeometry(0.11, 7.0, 24, 1, true), new THREE.MeshBasicMaterial({ color: index % 2 ? primary : secondary, transparent: true, opacity: 0.075, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    beam.position.y = 2.3;
    beam.rotation.z = (index - 2) * 0.42;
    group.add(beam);
    beams.push(beam);
  }
  const halo = new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.022, 8, 96), new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: 0.86, blending: THREE.AdditiveBlending, depthWrite: false }));
  halo.rotation.x = Math.PI * 0.42;
  group.add(halo);

  const shardCount = 1800;
  const positions = new Float32Array(shardCount * 3);
  const seeds = new Float32Array(shardCount * 3);
  for (let index = 0; index < shardCount; index++) {
    const angle = Math.random() * TAU;
    const radius = 1.2 + Math.pow(Math.random(), 0.55) * 5.6;
    seeds[index * 3] = angle; seeds[index * 3 + 1] = radius; seeds[index * 3 + 2] = (Math.random() - 0.5) * 2.0;
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = -1.4 + Math.random() * 5.4;
    positions[index * 3 + 2] = seeds[index * 3 + 2] - 1.0;
  }
  const shardGeometry = new THREE.BufferGeometry();
  shardGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const shardMaterial = new THREE.PointsMaterial({ color: primary, size: 0.042, transparent: true, opacity: 0.78, blending: THREE.AdditiveBlending, depthWrite: false });
  const shards = new THREE.Points(shardGeometry, shardMaterial);
  group.add(shards);
  group.userData = { towers, beams, halo, shards, shardMaterial, seeds, primary, secondary };
  return group;
}

export function updateCrystalCathedral(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { towers, beams, halo, shards, seeds } = group.userData;
  let mid = 0.20;
  let high = 0.14;
  if (frequencyData?.length) {
    const midStart = Math.floor(frequencyData.length * 0.18);
    const highStart = Math.floor(frequencyData.length * 0.58);
    let midSum = 0; let highSum = 0;
    for (let index = midStart; index < highStart; index++) midSum += frequencyData[index];
    for (let index = highStart; index < frequencyData.length; index++) highSum += frequencyData[index];
    mid = midSum / Math.max(1, (highStart - midStart) * 255);
    high = highSum / Math.max(1, (frequencyData.length - highStart) * 255);
  }
  towers.forEach(({ tower, material, edges, baseY, phase, angle }) => {
    tower.position.y = baseY + Math.sin(elapsedTime * (0.68 + mid) + phase) * (0.09 + mid * 0.22) + beatPulse * 0.12;
    tower.rotation.y = elapsedTime * 0.14 + angle;
    tower.scale.y = 1 + mid * 0.22 + beatPulse * 0.16;
    material.emissiveIntensity = 0.42 + mid * 1.15 + beatPulse * 0.65;
    edges.material.opacity = 0.46 + high * 0.42 + beatPulse * 0.20;
  });
  beams.forEach((beam, index) => { beam.rotation.y = elapsedTime * (0.09 + index * 0.025); beam.scale.x = 1 + mid * 0.7 + beatPulse * 0.38; beam.material.opacity = 0.035 + mid * 0.12 + beatPulse * 0.06; });
  halo.rotation.z += deltaTime * (0.28 + high * 0.72);
  halo.scale.setScalar(1 + beatPulse * 0.24 + mid * 0.08);
  const positions = shards.geometry.attributes.position.array;
  for (let index = 0; index < shards.geometry.attributes.position.count; index++) {
    const angle = seeds[index * 3] + elapsedTime * (0.08 + high * 0.22);
    const radius = seeds[index * 3 + 1];
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 2] = Math.sin(angle) * radius * 0.20 + seeds[index * 3 + 2] - 1.0;
  }
  shards.geometry.attributes.position.needsUpdate = true;
}

export function setCrystalCathedralColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { towers, beams, halo, shardMaterial, primary, secondary } = group.userData;
  primary.set(primaryValue); secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.45, 0.04, 0.05));
  towers.forEach(({ material, edges }, index) => { const color = index % 2 ? secondary : primary; material.color.copy(color); material.emissive.copy(color); edges.material.color.copy(color); });
  beams.forEach((beam, index) => beam.material.color.copy(index % 2 ? secondary : primary));
  halo.material.color.copy(primary); shardMaterial.color.copy(primary);
}
