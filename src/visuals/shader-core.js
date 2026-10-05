import * as THREE from 'three';

/**
 * GLSL Vertex Shader: Dynamic Audio Frequency Simplex/Perlin Noise Surface Displacement.
 * Bounded organic wave displacement with sleek proportions.
 */
const liquidChromeVertexShader = `
  uniform float uTime;
  uniform float uAudioBass;
  uniform float uAudioMid;
  uniform float uNoiseFrequency;
  uniform float uNoiseAmplitude;

  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec3 vEyeVector;
  varying float vDisplacement;

  // GLSL 3D Simplex Noise Function
  vec4 permute(vec4 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);

    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);

    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;

    i = mod(i, 289.0);
    vec4 p = permute(permute(permute(
              i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));

    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;

    vec4 j = p - 49.0 * floor(p * ns.z);

    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);

    vec4 x = x_ *ns.x + ns.yyyy;
    vec4 y = y_ *ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);

    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);

    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));

    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;

    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);

    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;

    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = position;

    float noise1 = snoise(position * uNoiseFrequency + vec3(uTime * 0.40));
    float noise2 = snoise(position * (uNoiseFrequency * 1.8) - vec3(uTime * 0.50));

    float audioDisp = (uAudioBass * 0.25) + (uAudioMid * 0.15);
    float displacement = (noise1 * 0.5 + noise2 * 0.3) * (uNoiseAmplitude + audioDisp);
    displacement = clamp(displacement, -0.20, 0.25);

    vDisplacement = displacement;

    vec3 newPosition = position + normal * displacement;

    vec4 worldPosition = modelMatrix * vec4(newPosition, 1.0);
    vEyeVector = normalize(worldPosition.xyz - cameraPosition);

    gl_Position = projectionMatrix * viewMatrix * worldPosition;
  }
`;

/**
 * GLSL Fragment Shader: Controlled Metallic Specular Highlights & Multi-Color Rim Lighting.
 */
const liquidChromeFragmentShader = `
  uniform float uTime;
  uniform vec3 uColorPrimary;
  uniform vec3 uColorSecondary;
  uniform vec3 uColorTertiary;
  uniform float uFresnelPower;
  uniform float uAudioHigh;

  varying vec3 vNormal;
  varying vec3 vPosition;
  varying vec3 vEyeVector;
  varying float vDisplacement;

  void main() {
    vec3 normal = normalize(vNormal);

    float fresnel = pow(1.0 + dot(vEyeVector, normal), uFresnelPower);
    fresnel = clamp(fresnel, 0.0, 1.0);

    vec3 lightDir = normalize(vec3(1.0, 2.0, 1.5));
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(-vEyeVector, reflectDir), 0.0), 32.0);

    float noiseMix = clamp((vDisplacement + 0.25) * 0.8, 0.0, 1.0);
    vec3 colorAB = mix(uColorPrimary, uColorSecondary, noiseMix);

    float timeMix = sin(uTime * 0.8 + vPosition.y * 1.2) * 0.5 + 0.5;
    vec3 finalBaseColor = mix(colorAB, uColorTertiary, timeMix * 0.4);

    vec3 metallicGlow = finalBaseColor * (0.50 + spec * 0.70);
    vec3 fresnelNeonRim = uColorSecondary * fresnel * (0.70 + uAudioHigh * 0.35);

    vec3 finalColor = clamp(metallicGlow + fresnelNeonRim, 0.0, 1.0);

    gl_FragColor = vec4(finalColor, 0.95);
  }
`;

/**
 * Creates Sleek 3D Liquid Chrome Shader Core Mesh (Radius = 0.90 for elegant proportions).
 * @param {number|string|THREE.Color} primaryColor 
 * @param {number|string|THREE.Color} secondaryColor 
 * @param {number|string|THREE.Color} tertiaryColor 
 * @returns {THREE.Mesh} Liquid Chrome Shader Core Mesh
 */
export function createLiquidChromeCore(primaryColor = 0xff00a0, secondaryColor = 0x00f3ff, tertiaryColor = 0xffaa00) {
  // Sleek geometry radius = 0.90 (elegant floating focal jewel)
  const geometry = new THREE.SphereGeometry(0.90, 128, 128);

  const material = new THREE.ShaderMaterial({
    vertexShader: liquidChromeVertexShader,
    fragmentShader: liquidChromeFragmentShader,
    uniforms: {
      uTime: { value: 0.0 },
      uAudioBass: { value: 0.0 },
      uAudioMid: { value: 0.0 },
      uAudioHigh: { value: 0.0 },
      uNoiseFrequency: { value: 0.90 },
      uNoiseAmplitude: { value: 0.18 },
      uFresnelPower: { value: 2.2 },
      uColorPrimary: { value: new THREE.Color(primaryColor) },
      uColorSecondary: { value: new THREE.Color(secondaryColor) },
      uColorTertiary: { value: new THREE.Color(tertiaryColor) }
    },
    transparent: true,
    depthWrite: true
  });

  const coreMesh = new THREE.Mesh(geometry, material);
  coreMesh.position.set(0, 1.5, 0);
  coreMesh.name = 'liquidChromeCoreMesh';
  coreMesh.userData = { material };
  return coreMesh;
}

/**
 * Updates GLSL Liquid Chrome Shader uniforms & beat reactivity per frame.
 * @param {THREE.Mesh} coreMesh 
 * @param {Uint8Array|null} frequencyData 
 * @param {number} deltaTime 
 * @param {number} elapsedTime 
 * @param {number} beatPulse 
 */
export function updateLiquidChromeCore(coreMesh, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0.0) {
  if (!coreMesh || !coreMesh.userData || !coreMesh.userData.material) return;

  const uniforms = coreMesh.userData.material.uniforms;
  uniforms.uTime.value = elapsedTime;

  let bass = beatPulse;
  let mid = 0.0;
  let high = 0.0;

  if (frequencyData && frequencyData.length > 0) {
    const len = frequencyData.length;
    let bSum = 0, mSum = 0, hSum = 0;
    for (let i = 0; i < Math.floor(len * 0.15); i++) bSum += frequencyData[i];
    for (let i = Math.floor(len * 0.15); i < Math.floor(len * 0.5); i++) mSum += frequencyData[i];
    for (let i = Math.floor(len * 0.5); i < len; i++) hSum += frequencyData[i];

    bass = Math.max(beatPulse, bSum / (len * 0.15 * 255.0));
    mid = mSum / (len * 0.35 * 255.0);
    high = hSum / (len * 0.5 * 255.0);
  }

  uniforms.uAudioBass.value = THREE.MathUtils.lerp(uniforms.uAudioBass.value, bass, deltaTime * 10.0);
  uniforms.uAudioMid.value = THREE.MathUtils.lerp(uniforms.uAudioMid.value, mid, deltaTime * 10.0);
  uniforms.uAudioHigh.value = THREE.MathUtils.lerp(uniforms.uAudioHigh.value, high, deltaTime * 10.0);

  // Elegant Scale Pulse on Beat Hit (clamped to max 1.15)
  const sphereScale = 1.0 + (bass * 0.15);
  coreMesh.scale.set(sphereScale, sphereScale, sphereScale);

  coreMesh.rotation.y = elapsedTime * 0.35;
  coreMesh.rotation.x = Math.sin(elapsedTime * 0.5) * 0.12;
}

/**
 * Updates Liquid Chrome Shader Colors dynamically based on AI predicted emotion.
 * @param {THREE.Mesh} coreMesh 
 * @param {number|THREE.Color} primary 
 * @param {number|THREE.Color} secondary 
 * @param {number|THREE.Color} tertiary 
 */
export function setLiquidChromeColors(coreMesh, primary, secondary, tertiary) {
  if (!coreMesh || !coreMesh.userData || !coreMesh.userData.material) return;

  const uniforms = coreMesh.userData.material.uniforms;

  if (primary !== undefined) {
    uniforms.uColorPrimary.value.lerp(new THREE.Color(primary), 0.25);
  }
  if (secondary !== undefined) {
    uniforms.uColorSecondary.value.lerp(new THREE.Color(secondary), 0.25);
  }
  if (tertiary !== undefined) {
    uniforms.uColorTertiary.value.lerp(new THREE.Color(tertiary), 0.25);
  }
}
