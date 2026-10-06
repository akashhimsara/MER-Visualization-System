import * as THREE from 'three';

const TAU = Math.PI * 2;

function petalCurve(angle, length, width, lift) {
  const direction = new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0);
  const side = new THREE.Vector3(-Math.sin(angle), Math.cos(angle), 0);
  return new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 0),
    direction.clone().multiplyScalar(length * 0.28).add(side.multiplyScalar(width)).setZ(lift * 0.34),
    direction.clone().multiplyScalar(length * 0.72).add(side.multiplyScalar(width * 0.38)).setZ(lift),
    direction.clone().multiplyScalar(length).setZ(lift * 0.48)
  ]);
}

/** Layered procedural flower for vocal, calm, and acoustic tracks. */
export function createNeonLotus() {
  const group = new THREE.Group();
  group.name = 'mode_neonLotus';
  group.position.y = 1.25;
  const primary = new THREE.Color(0x53f7e9);
  const secondary = new THREE.Color(0xff70d2);
  const petals = [];
  const layers = [
    { count: 12, length: 2.7, width: 0.72, lift: 0.46, rotation: 0.08 },
    { count: 10, length: 2.05, width: 0.56, lift: 0.82, rotation: Math.PI / 10 },
    { count: 8, length: 1.42, width: 0.38, lift: 1.02, rotation: 0.02 }
  ];
  layers.forEach((layer, layerIndex) => {
    for (let index = 0; index < layer.count; index++) {
      const angle = layer.rotation + (index / layer.count) * TAU;
      const material = new THREE.MeshBasicMaterial({ color: (index + layerIndex) % 2 ? secondary : primary, transparent: true, opacity: 0.74, blending: THREE.AdditiveBlending, depthWrite: false });
      const mesh = new THREE.Mesh(new THREE.TubeGeometry(petalCurve(angle, layer.length, layer.width, layer.lift), 32, 0.022 + layerIndex * 0.004, 6, false), material);
      group.add(mesh);
      petals.push({ mesh, material, angle, layerIndex, baseScale: 1 + layerIndex * 0.055 });
    }
  });
  const core = new THREE.Group();
  const inner = new THREE.Mesh(new THREE.SphereGeometry(0.25, 32, 16), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.72, blending: THREE.AdditiveBlending, depthWrite: false }));
  const halo = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.027, 8, 64), new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: 0.86, blending: THREE.AdditiveBlending, depthWrite: false }));
  halo.rotation.x = Math.PI * 0.30;
  core.add(inner, halo);
  group.add(core);
  const sparkleCount = 1150;
  const positions = new Float32Array(sparkleCount * 3);
  for (let index = 0; index < sparkleCount; index++) {
    const angle = Math.random() * TAU;
    const radius = 1.4 + Math.pow(Math.random(), 0.58) * 5.2;
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = Math.sin(angle) * radius * 0.62 + 0.4;
    positions[index * 3 + 2] = -0.7 - Math.random() * 1.7;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const sparkleMaterial = new THREE.PointsMaterial({ color: primary, size: 0.038, transparent: true, opacity: 0.78, blending: THREE.AdditiveBlending, depthWrite: false });
  const sparkles = new THREE.Points(geometry, sparkleMaterial);
  group.add(sparkles);
  group.userData = { petals, core, inner, halo, sparkles, sparkleMaterial, primary, secondary };
  return group;
}

export function updateNeonLotus(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { petals, core, halo, sparkles } = group.userData;
  let midEnergy = 0.22;
  let highEnergy = 0.16;
  if (frequencyData?.length) {
    const midStart = Math.floor(frequencyData.length * 0.18);
    const highStart = Math.floor(frequencyData.length * 0.58);
    let midSum = 0; let highSum = 0;
    for (let index = midStart; index < highStart; index++) midSum += frequencyData[index];
    for (let index = highStart; index < frequencyData.length; index++) highSum += frequencyData[index];
    midEnergy = midSum / Math.max(1, (highStart - midStart) * 255);
    highEnergy = highSum / Math.max(1, (frequencyData.length - highStart) * 255);
  }
  petals.forEach(({ mesh, angle, layerIndex, baseScale }) => {
    const breath = Math.sin(elapsedTime * (0.75 + layerIndex * 0.12) + angle * 2) * 0.035;
    const scale = baseScale + midEnergy * (0.12 + layerIndex * 0.025) + beatPulse * 0.10 + breath;
    mesh.scale.setScalar(scale);
    mesh.rotation.z = Math.sin(elapsedTime * 0.40 + angle) * 0.025 * (1 + midEnergy);
    mesh.material.opacity = 0.54 + midEnergy * 0.28 + beatPulse * 0.16;
  });
  core.rotation.z += deltaTime * (0.24 + midEnergy * 0.5);
  core.scale.setScalar(1 + midEnergy * 0.14 + beatPulse * 0.40);
  halo.rotation.z -= deltaTime * (0.42 + highEnergy);
  sparkles.rotation.z = elapsedTime * (0.045 + highEnergy * 0.13);
  sparkles.scale.setScalar(1 + highEnergy * 0.12 + beatPulse * 0.08);
  sparkles.material.opacity = 0.42 + highEnergy * 0.44;
}

export function setNeonLotusColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { petals, inner, halo, sparkleMaterial, primary, secondary } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.42, 0.06, 0.05));
  petals.forEach(({ material }, index) => material.color.copy(index % 2 ? secondary : primary));
  inner.material.color.copy(secondary);
  halo.material.color.copy(primary);
  sparkleMaterial.color.copy(primary);
}
