import * as THREE from 'three';

const TAU = Math.PI * 2;

function createDust(count, primary, secondary) {
  const positions = new Float32Array(count * 3);
  const seeds = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  for (let index = 0; index < count; index++) {
    const radius = 2.5 + Math.pow(Math.random(), 0.48) * 7.5;
    const angle = Math.random() * TAU;
    seeds[index * 3] = radius;
    seeds[index * 3 + 1] = angle;
    seeds[index * 3 + 2] = (Math.random() - 0.5) * 2.8;
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = Math.sin(angle) * radius * 0.62;
    positions[index * 3 + 2] = seeds[index * 3 + 2] - 1.2;
    const color = new THREE.Color(primary).lerp(new THREE.Color(secondary), Math.random());
    colors[index * 3] = color.r; colors[index * 3 + 1] = color.g; colors[index * 3 + 2] = color.b;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return { dust: new THREE.Points(geometry, new THREE.PointsMaterial({ size: 0.042, vertexColors: true, transparent: true, opacity: 0.82, blending: THREE.AdditiveBlending, depthWrite: false })), seeds };
}

/** Cinematic black-sun composition for reflective / emotional audio. */
export function createSolarEclipse() {
  const group = new THREE.Group();
  group.name = 'mode_solarEclipse';
  group.position.y = 1.45;
  const primary = new THREE.Color(0xffc85a);
  const secondary = new THREE.Color(0xad70ff);

  const corona = new THREE.Mesh(new THREE.RingGeometry(1.48, 1.77, 128), new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: 0.88, blending: THREE.AdditiveBlending, depthWrite: false }));
  const coronaOuter = new THREE.Mesh(new THREE.RingGeometry(1.84, 1.90, 128), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.46, blending: THREE.AdditiveBlending, depthWrite: false }));
  const blackSun = new THREE.Mesh(new THREE.CircleGeometry(1.47, 128), new THREE.MeshBasicMaterial({ color: 0x010106, transparent: true, opacity: 0.98, depthWrite: true }));
  corona.position.z = -0.03; coronaOuter.position.z = -0.04; blackSun.position.z = 0.05;
  group.add(corona, coronaOuter, blackSun);

  const arcs = [];
  [2.35, 3.10, 3.92].forEach((radius, index) => {
    const arc = new THREE.Mesh(new THREE.TorusGeometry(radius, 0.016 + index * 0.007, 8, 128), new THREE.MeshBasicMaterial({ color: index % 2 ? secondary : primary, transparent: true, opacity: 0.50 + index * 0.08, blending: THREE.AdditiveBlending, depthWrite: false }));
    arc.rotation.x = (index - 1) * 0.36;
    arc.rotation.y = index % 2 ? 0.28 : -0.18;
    group.add(arc);
    arcs.push({ arc, speed: (index % 2 ? -1 : 1) * (0.09 + index * 0.055) });
  });
  const { dust, seeds } = createDust(2800, primary, secondary);
  group.add(dust);
  group.userData = { corona, coronaOuter, blackSun, arcs, dust, seeds, primary, secondary };
  return group;
}

export function updateSolarEclipse(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { corona, coronaOuter, arcs, dust, seeds } = group.userData;
  let bass = beatPulse;
  let mid = 0.18;
  if (frequencyData?.length) {
    const bassEnd = Math.max(1, Math.floor(frequencyData.length * 0.16));
    const midEnd = Math.floor(frequencyData.length * 0.56);
    let bassSum = 0; let midSum = 0;
    for (let index = 0; index < bassEnd; index++) bassSum += frequencyData[index];
    for (let index = bassEnd; index < midEnd; index++) midSum += frequencyData[index];
    bass = Math.max(beatPulse, bassSum / (bassEnd * 255));
    mid = midSum / Math.max(1, (midEnd - bassEnd) * 255);
  }
  const coronaScale = 1 + bass * 0.34 + beatPulse * 0.20;
  corona.scale.setScalar(coronaScale);
  coronaOuter.scale.setScalar(1 + mid * 0.16 + beatPulse * 0.11);
  corona.rotation.z = elapsedTime * (0.10 + mid * 0.15);
  coronaOuter.rotation.z = -elapsedTime * (0.07 + mid * 0.10);
  arcs.forEach(({ arc, speed }, index) => {
    arc.rotation.z += speed * deltaTime * (1 + mid);
    arc.scale.setScalar(1 + beatPulse * (0.06 + index * 0.025));
  });
  const positions = dust.geometry.attributes.position.array;
  for (let index = 0; index < dust.geometry.attributes.position.count; index++) {
    const radius = seeds[index * 3];
    const angle = seeds[index * 3 + 1] + elapsedTime * (0.045 + 0.07 / radius);
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = Math.sin(angle) * radius * 0.62;
    positions[index * 3 + 2] = seeds[index * 3 + 2] - 1.2 + Math.sin(angle * 3 + elapsedTime) * 0.16;
  }
  dust.geometry.attributes.position.needsUpdate = true;
  dust.scale.setScalar(1 + beatPulse * 0.08);
}

export function setSolarEclipseColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { corona, coronaOuter, arcs, dust, primary, secondary } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.42, 0.06, 0.04));
  corona.material.color.copy(primary); coronaOuter.material.color.copy(secondary);
  arcs.forEach(({ arc }, index) => arc.material.color.copy(index % 2 ? secondary : primary));
  const colors = dust.geometry.attributes.color.array;
  for (let index = 0; index < dust.geometry.attributes.color.count; index++) {
    const mix = (index % 211) / 210;
    colors[index * 3] = primary.r + (secondary.r - primary.r) * mix;
    colors[index * 3 + 1] = primary.g + (secondary.g - primary.g) * mix;
    colors[index * 3 + 2] = primary.b + (secondary.b - primary.b) * mix;
  }
  dust.geometry.attributes.color.needsUpdate = true;
}
