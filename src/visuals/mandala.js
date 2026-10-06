import * as THREE from 'three';

const TAU = Math.PI * 2;

function createLine(points, color, opacity = 0.9) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false });
  return new THREE.LineLoop(geometry, material);
}

function starPoints(radius, points, innerRatio, rotation = 0) {
  const vertices = [];
  for (let index = 0; index < points * 2; index++) {
    const angle = rotation + (index / (points * 2)) * TAU;
    const currentRadius = index % 2 === 0 ? radius : radius * innerRatio;
    vertices.push(new THREE.Vector3(Math.cos(angle) * currentRadius, Math.sin(angle) * currentRadius, 0));
  }
  return vertices;
}

function circlePoints(radius, segments = 96) {
  const vertices = [];
  for (let index = 0; index < segments; index++) {
    const angle = (index / segments) * TAU;
    vertices.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, 0));
  }
  return vertices;
}

function createRibbon(count, color) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.52, blending: THREE.AdditiveBlending, depthWrite: false });
  return new THREE.Line(geometry, material);
}

/** A code-generated neon mandala with audio-reactive geometry and flow ribbons. */
export function createNeonMandala() {
  const group = new THREE.Group();
  group.name = 'mode_neonMandala';
  group.position.y = 1.45;

  const primary = new THREE.Color(0x35f6ff);
  const secondary = new THREE.Color(0xec5cff);
  const accent = new THREE.Color(0xa88bff);
  const layers = [];
  const layerSpecs = [
    { radius: 0.55, points: 8, inner: 0.43, color: primary, speed: 0.44 },
    { radius: 1.05, points: 10, inner: 0.60, color: secondary, speed: -0.28 },
    { radius: 1.58, points: 12, inner: 0.52, color: primary, speed: 0.19 },
    { radius: 2.18, points: 10, inner: 0.72, color: accent, speed: -0.12 },
    { radius: 2.72, points: 16, inner: 0.86, color: secondary, speed: 0.08 }
  ];

  layerSpecs.forEach((spec, index) => {
    const layer = new THREE.Group();
    const star = createLine(starPoints(spec.radius, spec.points, spec.inner, index * 0.18), spec.color, 0.86);
    const ring = createLine(circlePoints(spec.radius * (index % 2 ? 0.86 : 1.08)), spec.color, 0.42);
    layer.add(star, ring);
    group.add(layer);
    layers.push({ group: layer, materials: [star.material, ring.material], speed: spec.speed, baseScale: 1 + index * 0.035 });
  });

  const centre = new THREE.Group();
  const centreRing = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.022, 8, 64), new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending }));
  const centreGlow = new THREE.Mesh(new THREE.CircleGeometry(0.18, 48), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.42, blending: THREE.AdditiveBlending, depthWrite: false }));
  centre.add(centreRing, centreGlow);
  group.add(centre);

  const ribbons = [];
  for (let index = 0; index < 16; index++) {
    const ribbon = createRibbon(110, index % 2 === 0 ? primary : secondary);
    ribbon.position.z = -0.15 - index * 0.006;
    group.add(ribbon);
    ribbons.push({ ribbon, index, material: ribbon.material });
  }

  const starCount = 760;
  const positions = new Float32Array(starCount * 3);
  for (let index = 0; index < starCount; index++) {
    const angle = Math.random() * TAU;
    const radius = 2.9 + Math.pow(Math.random(), 0.58) * 4.8;
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = Math.sin(angle) * radius;
    positions[index * 3 + 2] = -0.5 - Math.random() * 1.2;
  }
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const starMaterial = new THREE.PointsMaterial({ color: primary, size: 0.035, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false });
  const stars = new THREE.Points(starGeometry, starMaterial);
  group.add(stars);

  group.userData = { layers, centre, centreRing, centreGlow, ribbons, stars, starMaterial, primary, secondary };
  return group;
}

export function updateNeonMandala(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0) {
  if (!group?.userData) return;
  const { layers, centre, ribbons, stars } = group.userData;
  let midEnergy = 0.28;
  let highEnergy = 0.18;
  if (frequencyData?.length) {
    const midStart = Math.floor(frequencyData.length * 0.18);
    const midEnd = Math.floor(frequencyData.length * 0.55);
    let midSum = 0;
    let highSum = 0;
    for (let index = midStart; index < midEnd; index++) midSum += frequencyData[index];
    for (let index = midEnd; index < frequencyData.length; index++) highSum += frequencyData[index];
    midEnergy = midSum / Math.max(1, (midEnd - midStart) * 255);
    highEnergy = highSum / Math.max(1, (frequencyData.length - midEnd) * 255);
  }
  layers.forEach(({ group: layer, speed, baseScale }, index) => {
    layer.rotation.z += speed * deltaTime * (1 + midEnergy * 1.4);
    layer.scale.setScalar(baseScale * (1 + beatPulse * (0.045 + index * 0.009)));
  });
  centre.scale.setScalar(1 + beatPulse * 0.30 + midEnergy * 0.08);
  centre.rotation.z = elapsedTime * 0.45;
  stars.rotation.z = elapsedTime * 0.025;
  stars.scale.setScalar(1 + beatPulse * 0.07);
  ribbons.forEach(({ ribbon, index }) => {
    const positions = ribbon.geometry.attributes.position.array;
    const direction = (index / ribbons.length) * TAU;
    const phase = elapsedTime * (0.72 + (index % 3) * 0.14) + index * 0.77;
    for (let point = 0; point < 110; point++) {
      const t = point / 109;
      const radius = 2.3 + t * 5.2;
      const wave = Math.sin(t * 9.0 + phase) * (0.22 + highEnergy * 0.45);
      const angle = direction + wave + Math.sin(t * 4 + phase * 0.65) * 0.12;
      positions[point * 3] = Math.cos(angle) * radius;
      positions[point * 3 + 1] = Math.sin(angle) * radius;
      positions[point * 3 + 2] = -0.1 - t * 0.5;
    }
    ribbon.geometry.attributes.position.needsUpdate = true;
    ribbon.material.opacity = 0.32 + highEnergy * 0.34 + beatPulse * 0.18;
  });
}

export function setNeonMandalaColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { layers, centreRing, centreGlow, ribbons, starMaterial, primary, secondary } = group.userData;
  primary.set(primaryValue);
  secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.48, 0, 0));
  layers.forEach(({ materials }, index) => materials.forEach((material, materialIndex) => material.color.copy((index + materialIndex) % 2 === 0 ? primary : secondary)));
  ribbons.forEach(({ material, index }) => material.color.copy(index % 2 === 0 ? primary : secondary));
  centreRing.material.color.copy(primary);
  centreGlow.material.color.copy(secondary);
  starMaterial.color.copy(primary);
}
