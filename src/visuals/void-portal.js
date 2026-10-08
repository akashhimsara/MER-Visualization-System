import * as THREE from 'three';

const TAU = Math.PI * 2;
const clamp01 = (value) => Math.max(0, Math.min(1, value));
const smoothstep = (value) => { const t = clamp01(value); return t * t * (3 - 2 * t); };

function createIrisMaterial(primary, secondary) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uReveal: { value: 0 }, uEnergy: { value: 0 }, uPrimary: { value: new THREE.Color(primary) }, uSecondary: { value: new THREE.Color(secondary) } },
    vertexShader: 'varying vec2 vUv; void main(){vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader: `varying vec2 vUv; uniform float uTime; uniform float uReveal; uniform float uEnergy; uniform vec3 uPrimary; uniform vec3 uSecondary;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);} float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.,1.)),f.x),f.y);} float fbm(vec2 p){float v=0.;float a=.5;for(int i=0;i<4;i++){v+=a*noise(p);p=p*2.02+5.7;a*=.5;}return v;}
      void main(){ vec2 p=vUv*2.0-1.0; float r=length(p); if(r>1.0 || r<0.36) discard; float a=atan(p.y,p.x); float n=fbm(vec2(a*2.2+r*3.0,uTime*.13-r*4.0));
      float wisps=.5+.5*sin(a*10.0+r*14.0+n*9.0-uTime*(.6+uEnergy*1.7)); float filaments=.5+.5*sin(a*26.0-r*11.0+n*5.0+uTime*.3);
      float texture=.32+n*.34+wisps*.20+filaments*.10; float edge=smoothstep(.37,.50,r)*(1.0-smoothstep(.79,1.0,r));
      vec3 col=mix(uPrimary,uSecondary,.5+.5*sin(a*1.8-r*5.0+n*3.0+uTime*.42)); float alpha=texture*edge*(.34+uEnergy*.55)*uReveal; gl_FragColor=vec4(col,alpha); }`
  });
}

function createSparkles(count, color) {
  const positions = new Float32Array(count * 3);
  const seeds = new Float32Array(count * 3);
  for (let index = 0; index < count; index++) {
    const angle = Math.random() * TAU;
    const radius = 3.6 + Math.pow(Math.random(), 0.50) * 4.6;
    seeds[index * 3] = angle; seeds[index * 3 + 1] = radius; seeds[index * 3 + 2] = Math.random() * TAU;
    positions[index * 3] = Math.cos(angle) * radius;
    positions[index * 3 + 1] = Math.sin(angle) * radius * 0.60;
    positions[index * 3 + 2] = -1.4 - Math.random() * 1.4;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  return { sparkles: new THREE.Points(geometry, new THREE.PointsMaterial({ color, size: 0.026, transparent: true, opacity: 0.74, blending: THREE.AdditiveBlending, depthWrite: false })), seeds };
}

/** A restrained, centre-focused sci-fi iris: a portal that feels alive, not a tunnel diagram. */
export function createVoidPortal() {
  const group = new THREE.Group();
  group.name = 'mode_voidPortal';
  group.position.y = 1.45;
  group.scale.y = 0.78;
  const primary = new THREE.Color(0xff38bd);
  const secondary = new THREE.Color(0x49f3ff);

  const backdrop = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), new THREE.MeshBasicMaterial({ color: 0x020407, transparent: true, opacity: 0.98, depthWrite: false }));
  backdrop.position.z = -3.4;
  group.add(backdrop);

  const pupil = new THREE.Mesh(new THREE.CircleGeometry(1.18, 96), new THREE.MeshBasicMaterial({ color: 0x010106, transparent: true, opacity: 0.99, depthWrite: true }));
  pupil.position.z = 0.12;
  const innerHalo = new THREE.Mesh(new THREE.RingGeometry(1.18, 1.205, 96), new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.34, blending: THREE.AdditiveBlending, depthWrite: false }));
  const outerHalo = new THREE.Mesh(new THREE.RingGeometry(2.78, 2.795, 128), new THREE.MeshBasicMaterial({ color: primary, transparent: true, opacity: 0.08, blending: THREE.AdditiveBlending, depthWrite: false }));
  group.add(outerHalo, pupil);

  const irisMaterial = createIrisMaterial(primary, secondary);
  const iris = new THREE.Mesh(new THREE.CircleGeometry(2.78, 128), irisMaterial);
  iris.position.z = -0.04;
  group.add(iris);

  const orbitRings = [];

  const { sparkles, seeds: sparkleSeeds } = createSparkles(420, primary);
  group.add(sparkles);
  const shockwaves = Array.from({ length: 3 }, (_, index) => {
    const mesh = new THREE.Mesh(new THREE.RingGeometry(1.20, 1.25, 96), new THREE.MeshBasicMaterial({ color: index % 2 ? secondary : primary, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
    mesh.visible = false; group.add(mesh);
    return { mesh, age: 99, active: false };
  });
  group.userData = { backdrop, pupil, innerHalo, outerHalo, iris, irisMaterial, orbitRings, sparkles, sparkleSeeds, shockwaves, primary, secondary, introStart: null, outroStart: null, lastBeatPulse: 0 };
  return group;
}

export function startVoidPortalIntro(group, elapsedTime = 0) {
  if (!group?.userData) return;
  group.userData.introStart = elapsedTime;
  group.userData.outroStart = null;
  group.userData.lastBeatPulse = 0;
  group.userData.shockwaves.forEach(wave => { wave.active = false; wave.mesh.visible = false; });
}

export function startVoidPortalOutro(group, elapsedTime = 0) {
  if (!group?.userData) return;
  group.userData.outroStart = elapsedTime;
}

export function armVoidPortalIntro(group) {
  if (!group?.userData) return;
  group.userData.introStart = null;
  group.userData.lastBeatPulse = 0;
}

export function updateVoidPortal(group, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0, chapter = { key: 'FLOW', intensity: 0.2 }) {
  if (!group?.userData) return;
  const { backdrop, pupil, innerHalo, outerHalo, iris, irisMaterial, orbitRings, sparkles, sparkleSeeds, shockwaves } = group.userData;
  const introElapsed = group.userData.introStart === null ? -99 : elapsedTime - group.userData.introStart;
  const outroElapsed = group.userData.outroStart === null ? -99 : elapsedTime - group.userData.outroStart;
  const reveal = smoothstep(introElapsed / 3.4) * (1 - smoothstep(outroElapsed / 2.2));
  let bass = beatPulse; let mid = 0.20; let high = 0.14;
  if (frequencyData?.length) {
    const bassEnd = Math.max(1, Math.floor(frequencyData.length * 0.16));
    const highStart = Math.floor(frequencyData.length * 0.58);
    let bassSum = 0; let midSum = 0; let highSum = 0;
    for (let index = 0; index < bassEnd; index++) bassSum += frequencyData[index];
    for (let index = bassEnd; index < highStart; index++) midSum += frequencyData[index];
    for (let index = highStart; index < frequencyData.length; index++) highSum += frequencyData[index];
    bass = Math.max(beatPulse, bassSum / (bassEnd * 255));
    mid = midSum / Math.max(1, (highStart - bassEnd) * 255);
    high = highSum / Math.max(1, (frequencyData.length - highStart) * 255);
  }
  const chapterStyle = {
    DORMANT: { iris: 0.72, sparkle: 0.08, halo: 0.04, rays: 0 },
    FLOW: { iris: 1.00, sparkle: 0.30, halo: 0.08, rays: 0 },
    BUILD: { iris: 1.05, sparkle: 0.52, halo: 0.18, rays: 0.06 },
    SURGE: { iris: 1.13, sparkle: 0.88, halo: 0.38 },
    RELEASE: { iris: 0.84, sparkle: 0.18, halo: 0.06, rays: 0 }
  }[chapter.key] || { iris: 1, sparkle: .3, halo: .08, rays: 0 };
  const pupilScale = 0.62 + reveal * 0.46 - bass * 0.35 - beatPulse * 0.25;
  backdrop.material.opacity = 0.98 * reveal;
  pupil.scale.setScalar(pupilScale);
  pupil.material.opacity = 0.99 * reveal;
  iris.scale.setScalar(chapterStyle.iris * (1 + beatPulse * 0.045));
  innerHalo.scale.setScalar((0.22 + reveal * 0.78) * (1 + bass * 0.18 + beatPulse * 0.24));
  // No permanent UI-like ring: it appears only as a short white/cyan kick flash.
  innerHalo.material.opacity = beatPulse * 0.26 * reveal;
  outerHalo.scale.setScalar((0.35 + reveal * 0.65) * (1 + mid * 0.05));
  outerHalo.material.opacity = (chapterStyle.halo + high * 0.055 + beatPulse * 0.12) * reveal;
  innerHalo.rotation.z -= deltaTime * (0.60 + high * 1.7);
  outerHalo.rotation.z += deltaTime * (0.08 + mid * 0.28);

  irisMaterial.uniforms.uTime.value = elapsedTime;
  irisMaterial.uniforms.uReveal.value = reveal;
  const chapterBoost = chapter.key === 'SURGE' ? 0.42 : chapter.key === 'BUILD' ? 0.22 : chapter.key === 'DORMANT' ? -0.16 : 0;
  irisMaterial.uniforms.uEnergy.value = Math.max(0, Math.min(1, mid * 0.65 + high * 0.35 + beatPulse * 0.35 + chapterBoost));
  orbitRings.forEach(({ ring, baseOpacity, speed }, index) => {
    ring.rotation.z += speed * deltaTime * (1 + mid * 1.5);
    ring.scale.setScalar((0.28 + reveal * 0.72) * (1 + beatPulse * (0.08 + index * 0.03)));
    ring.material.opacity = baseOpacity * reveal;
  });
  const sparklePositions = sparkles.geometry.attributes.position.array;
  for (let index = 0; index < sparkles.geometry.attributes.position.count; index++) {
    const angle = sparkleSeeds[index * 3] + elapsedTime * (0.035 + high * 0.17);
    const radius = sparkleSeeds[index * 3 + 1] * (0.30 + reveal * 0.70);
    sparklePositions[index * 3] = Math.cos(angle) * radius;
    sparklePositions[index * 3 + 1] = Math.sin(angle) * radius * 0.60;
  }
  sparkles.geometry.attributes.position.needsUpdate = true;
  sparkles.material.opacity = (chapterStyle.sparkle + high * 0.38) * reveal;
  sparkles.scale.setScalar(1 + (chapter.key === 'SURGE' ? 0.13 : 0) + beatPulse * 0.12);

  if (beatPulse > 0.30 && beatPulse > group.userData.lastBeatPulse + 0.12 && reveal > 0.88) {
    const wave = shockwaves.find(item => !item.active) || shockwaves[0];
    wave.active = true; wave.age = 0; wave.mesh.visible = true; wave.mesh.scale.setScalar(1);
  }
  group.userData.lastBeatPulse = beatPulse;
  shockwaves.forEach((wave, index) => {
    if (!wave.active) return;
    wave.age += deltaTime;
    const life = wave.age / 0.56;
    if (life >= 1) { wave.active = false; wave.mesh.visible = false; return; }
    wave.mesh.scale.setScalar(1 + life * (3.6 + index * 0.6));
    wave.mesh.material.opacity = (1 - life) * 0.86;
  });
}

export function setVoidPortalColors(group, primaryValue, secondaryValue) {
  if (!group?.userData || primaryValue === undefined) return;
  const { innerHalo, outerHalo, irisMaterial, orbitRings, sparkles, shockwaves, primary, secondary } = group.userData;
  primary.set(primaryValue); secondary.set(secondaryValue ?? new THREE.Color(primaryValue).offsetHSL(0.44, 0.05, 0.04));
  innerHalo.material.color.copy(secondary); outerHalo.material.color.copy(primary);
  orbitRings.forEach(({ ring }, index) => ring.material.color.copy(index % 2 ? secondary : primary));
  shockwaves.forEach(({ mesh }, index) => mesh.material.color.copy(index % 2 ? secondary : primary));
  sparkles.material.color.copy(primary);
  irisMaterial.uniforms.uPrimary.value.copy(primary);
  irisMaterial.uniforms.uSecondary.value.copy(secondary);
}
