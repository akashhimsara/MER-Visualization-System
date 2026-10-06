import * as THREE from 'three';

function createVortexParticles(count, primary, secondary) {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const seeds = new Float32Array(count * 3);
  const colorA = new THREE.Color(primary);
  const colorB = new THREE.Color(secondary);

  for (let index = 0; index < count; index++) {
    const radius = 0.65 + Math.pow(Math.random(), 0.55) * 6.1;
    const angle = Math.random() * Math.PI * 2;
    const mix = Math.random();
    const color = colorA.clone().lerp(colorB, mix);
    seeds[index * 3] = radius;
    seeds[index * 3 + 1] = angle;
    seeds[index * 3 + 2] = (Math.random() - 0.5) * 1.1;
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = Math.sin(angle) * radius;
    positions[index * 3 + 2] = seeds[index * 3 + 2];
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({ size: 0.048, vertexColors: true, transparent: true, opacity: 0.90, blending: THREE.AdditiveBlending, depthWrite: false });
  return { particles: new THREE.Points(geometry, material), seeds };
}

/** A deep-space portal with nested rings and particles orbiting into the void. */
export function createVoidPortal() {
  const group = new THREE.Group();
  group.name = 'mode_voidPortal';
  group.position.y = 1.45;
  const primary = new THREE.Color(0xff38bd);
  const secondary = new THREE.Color(0x49f3ff);
  const rings = [];

  for (let index = 0; index < 9; index++) {
    const radius = 0.78 + index * 0.42;
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(radius, 0.018 + (index % 3) * 0.008, 8, 96),
      new THREE.MeshBasicMaterial({ color: index % 2 ? primary : secondary, transparent: true, opacity: 0.32 + index * 0.055, blending: THREE.AdditiveBlending, depthWrite: false })
    );
    ring.rotation.x = (index % 3 - 1) * 0.22;
    ring.rotation.y = (index % 2 ? 1 : -1) * 0.16;
    group.add(ring);
    rings.push({ ring, material: ring.material, radius, speed: (index % 2 ? -1 : 1) * (0.16 + index * 0.07) });
  }

  const voidDisk = new THREE.Mesh(
    new THREE.CircleGeometry(0.73, 96),
    new THREE.MeshBasicMaterial({ color: 0x010108, transparent: true, opacity: 0.95, depthWrite: true })
  );
  voidDisk.position.z = 0.06;
  group.add(voidDisk);

  const coreHalo = new THREE.Mesh(
    new THREE.RingGeometry(0.72, 0.92, 96),
    new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  coreHalo.position.z = 0.07;
  group.add(coreHalo);

  const { particles, seeds } = createVortexParticles(5200, primary, secondary);
  particles.position.z = -0.1;
  group.add(particles);
  group.userData = { rings, voidDisk, coreHalo, particles, seeds, primary, secondary };
  return group;
}

export function updateVoidPortal(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { rings, coreHalo, particles, seeds } = group.userData;
  let bass = beatPulse;
  let high = 0.18;
  if (frequencyData?.length) {
    const bassEnd = Math.max(1, Math.floor(frequencyData.length * 0.16));
    const highStart = Math.floor(frequencyData.length * 0.58);
    let bassSum = 0;
    let highSum = 0;
    for (let index = 0; index < bassEnd; index++) bassSum += frequencyData[index];
    for (let index = highStart; index < frequencyData.length; index++) highSum += frequencyData[index];
    bass = Math.max(beatPulse, bassSum / (bassEnd * 255));
    high = highSum / Math.max(1, (frequencyData.length - highStart) * 255);
  }

  rings.forEach(({ ring, radius, speed }, index) => {
    ring.rotation.z += speed * deltaTime * (1 + bass * 2.3);
    const scale = 1 + beatPulse * (0.10 + index * 0.008);
    ring.scale.setScalar(scale);
    ring.position.z = Math.sin(elapsedTime * 0.65 + index) * 0.16;
  });
  coreHalo.rotation.z -= deltaTime * (0.6 + high * 2.4);
  coreHalo.scale.setScalar(1 + bass * 0.55);

  const positions = particles.geometry.attributes.position.array;
  for (let index = 0; index < particles.geometry.attributes.position.count; index++) {
    const radius = seeds[index * 3];
    const baseAngle = seeds[index * 3 + 1];
    const depth = seeds[index * 3 + 2];
    const twist = elapsedTime * (0.68 + (6.8 - radius) * 0.085) + radius * 0.90;
    const currentRadius = radius * (1 + Math.sin(elapsedTime * 0.75 + index * 0.07) * 0.035 + bass * 0.045);
    positions[index * 3] = Math.cos(baseAngle + twist) * currentRadius;
    positions[index * 3 + 1] = Math.sin(baseAngle + twist) * currentRadius;
    positions[index * 3 + 2] = depth + Math.sin(twist * 1.6) * 0.32;
  }
  particles.geometry.attributes.position.needsUpdate = true;
  particles.scale.setScalar(1 + beatPulse * 0.13);
}

export function setVoidPortalColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { rings, coreHalo, particles, primary, secondary } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.44, 0.05, 0.04));
  rings.forEach(({ material }, index) => material.color.copy(index % 2 ? primary : secondary));
  coreHalo.material.color.copy(primary);
  const colors = particles.geometry.attributes.color.array;
  for (let index = 0; index < particles.geometry.attributes.color.count; index++) {
    const mix = (index % 173) / 172;
    colors[index * 3] = primary.r + (secondary.r - primary.r) * mix;
    colors[index * 3 + 1] = primary.g + (secondary.g - primary.g) * mix;
    colors[index * 3 + 2] = primary.b + (secondary.b - primary.b) * mix;
  }
  particles.geometry.attributes.color.needsUpdate = true;
}
