import * as THREE from 'three';

function lineFromCurve(points, color, opacity = 0.8) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false });
  return new THREE.Line(geometry, material);
}

function branchCurve(side, height, reach, bend) {
  return new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -2.7, 0),
    new THREE.Vector3(side * 0.12, -0.7, 0.05),
    new THREE.Vector3(side * bend, height - 1.2, 0.1),
    new THREE.Vector3(side * reach, height, 0)
  ]).getPoints(48);
}

function ringPoints(radius, segments = 96) {
  const points = [];
  for (let index = 0; index < segments; index++) {
    const angle = (index / segments) * Math.PI * 2;
    points.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, 0));
  }
  return points;
}

/**
 * A procedural luminous tree/bloom inspired by sacred-geometry artwork.
 * It uses only generated lines, points, and orbit circles, so it remains
 * lightweight and fully beat-reactive.
 */
export function createCosmicBloom() {
  const group = new THREE.Group();
  group.name = 'mode_cosmicBloom';
  group.position.y = 1.4;

  const primary = new THREE.Color(0x33f7e7);
  const secondary = new THREE.Color(0xac6bff);
  const branches = [];
  const configs = [
    { height: 2.9, reach: 2.7, bend: 0.82 },
    { height: 2.2, reach: 3.45, bend: 1.45 },
    { height: 1.45, reach: 3.85, bend: 1.90 },
    { height: 0.70, reach: 3.35, bend: 1.65 }
  ];
  configs.forEach((config, branchIndex) => {
    [-1, 1].forEach(side => {
      const branch = lineFromCurve(branchCurve(side, config.height, config.reach, config.bend), branchIndex % 2 === 0 ? primary : secondary, 0.82);
      group.add(branch);
      branches.push({ line: branch, material: branch.material, side, branchIndex });
    });
  });

  const trunk = lineFromCurve(new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -3.1, 0), new THREE.Vector3(-0.12, -1.1, 0), new THREE.Vector3(0.16, 0.65, 0), new THREE.Vector3(0, 3.55, 0)
  ]).getPoints(68), primary, 0.92);
  group.add(trunk);

  const orbits = [];
  [1.3, 2.45, 3.65].forEach((radius, index) => {
    const orbit = lineFromCurve(ringPoints(radius), index % 2 ? secondary : primary, 0.44);
    orbit.rotation.x = index === 0 ? 0.36 : -0.18;
    group.add(orbit);
    orbits.push({ line: orbit, material: orbit.material, speed: (index % 2 ? -1 : 1) * (0.12 + index * 0.05) });
  });

  const leafCount = 880;
  const positions = new Float32Array(leafCount * 3);
  const basePositions = new Float32Array(leafCount * 3);
  for (let index = 0; index < leafCount; index++) {
    const side = index % 2 === 0 ? 1 : -1;
    const branch = configs[index % configs.length];
    const t = 0.16 + Math.random() * 0.82;
    const x = side * (t * branch.reach + (Math.random() - 0.5) * 0.65);
    const y = -2.4 + t * (branch.height + 2.4) + (Math.random() - 0.5) * 0.52;
    const z = (Math.random() - 0.5) * 0.65;
    positions[index * 3] = basePositions[index * 3] = x;
    positions[index * 3 + 1] = basePositions[index * 3 + 1] = y;
    positions[index * 3 + 2] = basePositions[index * 3 + 2] = z;
  }
  const leafGeometry = new THREE.BufferGeometry();
  leafGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const leafMaterial = new THREE.PointsMaterial({ color: primary, size: 0.06, transparent: true, opacity: 0.76, blending: THREE.AdditiveBlending, depthWrite: false });
  const leaves = new THREE.Points(leafGeometry, leafMaterial);
  group.add(leaves);

  const heart = new THREE.Mesh(new THREE.CircleGeometry(0.24, 48), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.78, blending: THREE.AdditiveBlending, depthWrite: false }));
  heart.position.y = -0.65;
  group.add(heart);

  group.userData = { branches, trunk, orbits, leaves, leafMaterial, basePositions, heart, primary, secondary };
  return group;
}

export function updateCosmicBloom(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { branches, orbits, leaves, basePositions, heart } = group.userData;
  let midEnergy = 0.24;
  if (frequencyData?.length) {
    const start = Math.floor(frequencyData.length * 0.17);
    const end = Math.floor(frequencyData.length * 0.58);
    let sum = 0;
    for (let index = start; index < end; index++) sum += frequencyData[index];
    midEnergy = sum / Math.max(1, (end - start) * 255);
  }
  branches.forEach(({ line, branchIndex, side }) => {
    line.rotation.z = Math.sin(elapsedTime * (0.45 + branchIndex * 0.08) + branchIndex) * 0.035 * side * (1 + midEnergy);
    line.scale.setScalar(1 + beatPulse * 0.045);
  });
  orbits.forEach(({ line, speed }, index) => {
    line.rotation.z += speed * deltaTime * (1 + midEnergy);
    line.scale.setScalar(1 + beatPulse * (0.035 + index * 0.015));
  });
  const position = leaves.geometry.attributes.position.array;
  for (let index = 0; index < leaves.geometry.attributes.position.count; index++) {
    const phase = elapsedTime * 0.9 + index * 0.17;
    position[index * 3] = basePositions[index * 3] + Math.sin(phase) * (0.025 + midEnergy * 0.09);
    position[index * 3 + 1] = basePositions[index * 3 + 1] + Math.cos(phase * 0.8) * (0.025 + midEnergy * 0.08) + beatPulse * 0.05;
  }
  leaves.geometry.attributes.position.needsUpdate = true;
  leaves.scale.setScalar(1 + beatPulse * 0.10);
  heart.scale.setScalar(1 + beatPulse * 0.42 + midEnergy * 0.12);
}

export function setCosmicBloomColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { branches, trunk, orbits, leafMaterial, heart, primary, secondary } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.42, 0.04, 0.04));
  branches.forEach(({ material, branchIndex }) => material.color.copy(branchIndex % 2 ? secondary : primary));
  trunk.material.color.copy(primary);
  orbits.forEach(({ material }, index) => material.color.copy(index % 2 ? secondary : primary));
  leafMaterial.color.copy(primary);
  heart.material.color.copy(secondary);
}
