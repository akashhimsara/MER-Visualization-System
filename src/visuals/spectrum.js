import * as THREE from 'three';

/**
 * Creates 3D Circular Glass Equalizer Bar Array with Top Peak Caps.
 * 64 3D Box Geometry towers arranged in a precision ring around origin.
 * 
 * @param {number} barCount - Number of equalizer towers (default: 64)
 * @param {number} ringRadius - Radius of equalizer ring (default: 3.6)
 * @returns {THREE.Group} Group containing 3D Equalizer Bar system
 */
export function createEqualizerRing(barCount = 64, ringRadius = 3.6) {
  const group = new THREE.Group();
  group.name = 'spectrumRing';

  const bars = [];
  const barWidth = 0.18;
  const barDepth = 0.18;
  const baseHeight = 0.15;

  // Main Bar Box Geometry (pivot at bottom y=0)
  const boxGeo = new THREE.BoxGeometry(barWidth, 1.0, barDepth);
  boxGeo.translate(0, 0.5, 0);

  // Top Peak Cap Indicator Geometry
  const capGeo = new THREE.BoxGeometry(barWidth * 1.15, 0.04, barDepth * 1.15);

  for (let i = 0; i < barCount; i++) {
    const angle = (i / barCount) * Math.PI * 2;
    const x = Math.cos(angle) * ringRadius;
    const z = Math.sin(angle) * ringRadius;

    // Color gradient along circular ring: Neon Cyan -> Royal Violet -> Sun Gold -> Neon Cyan
    const hue = (i / barCount);
    const color = new THREE.Color().setHSL(hue, 0.95, 0.55);

    const barMat = new THREE.MeshStandardMaterial({
      color: color,
      emissive: 0x000000, // Zero emissive blowout! Pure saturated neon color
      roughness: 0.15,
      metalness: 0.4,
      transparent: true,
      opacity: 0.95
    });

    const barMesh = new THREE.Mesh(boxGeo, barMat);
    barMesh.position.set(x, 0, z);
    barMesh.lookAt(0, 0, 0);

    // Top peak cap indicator mesh
    const capMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending
    });
    const capMesh = new THREE.Mesh(capGeo, capMat);
    capMesh.position.set(0, baseHeight, 0);
    barMesh.add(capMesh);

    group.add(barMesh);

    bars.push({
      mesh: barMesh,
      capMesh: capMesh,
      material: barMat,
      capMaterial: capMat,
      baseColor: color,
      angle: angle,
      index: i,
      targetHeight: baseHeight,
      currentHeight: baseHeight,
      peakHeight: baseHeight
    });
  }

  // Inner glowing central floor ring anchor
  const ringGeo = new THREE.RingGeometry(ringRadius - 0.04, ringRadius + 0.04, 64);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x00f3ff,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending
  });
  const ringMesh = new THREE.Mesh(ringGeo, ringMat);
  ringMesh.rotation.x = Math.PI * 0.5;
  ringMesh.position.y = 0.01;
  group.add(ringMesh);

  group.userData = { bars, barCount, ringRadius, ringMesh, baseHeight };
  return group;
}

/**
 * Backwards compatibility alias for createSpectrumRing.
 */
export function createSpectrumRing() {
  return createEqualizerRing(64, 3.6);
}

/**
 * Updates 3D Equalizer Bar heights in real-time based on Web Audio API FFT frequency data.
 * Fast Attack / Smooth Decay audio dynamics.
 * 
 * @param {THREE.Group} equalizerGroup 
 * @param {Uint8Array|null} frequencyData - Web Audio API byte frequency array (0-255)
 * @param {number} deltaTime 
 * @param {number} elapsedTime
 * @param {number} beatPulse
 */
export function updateSpectrumRing(equalizerGroup, frequencyData, deltaTime = 0.016, elapsedTime = 0, beatPulse = 0.0) {
  if (!equalizerGroup || !equalizerGroup.userData || !equalizerGroup.userData.bars) return;

  const { bars, barCount, baseHeight } = equalizerGroup.userData;
  const freqLength = frequencyData ? frequencyData.length : 0;
  const halfCount = Math.floor(barCount / 2);

  for (let i = 0; i < barCount; i++) {
    const bar = bars[i];
    let freqVal = 0.0;

    if (frequencyData && freqLength > 0) {
      // Symmetrical bin index mapping so Bass/Kick drum punches up symmetrically!
      const symIndex = i < halfCount ? i : (barCount - 1 - i);
      const binIndex = Math.floor((symIndex / halfCount) * (freqLength * 0.65));
      const rawByte = frequencyData[binIndex] || 0;
      // Exponential frequency response for punchy beat feel
      freqVal = Math.pow(rawByte / 255.0, 1.3);
    } else {
      // Demo audio frequency rhythm (snappy 128 BPM pulse wave)
      const symIndex = i < halfCount ? i : (barCount - 1 - i);
      const pulseWave = Math.sin(elapsedTime * 8.0 - symIndex * 0.2) * 0.5 + 0.5;
      const rippleWave = Math.cos(elapsedTime * 4.0 + symIndex * 0.4) * 0.5 + 0.5;
      freqVal = (pulseWave * 0.6 + rippleWave * 0.4) * (0.35 + beatPulse * 0.65);
    }

    // Dynamic tower height (0.15 to 4.2 units tall)
    const targetH = baseHeight + (freqVal * 4.2) + (beatPulse * 0.75);

    // Fast Attack (snaps up on beat hit), Smooth Elastic Decay (glides down)
    const lerpSpeed = targetH > bar.currentHeight ? deltaTime * 38.0 : deltaTime * 14.0;
    bar.currentHeight = THREE.MathUtils.lerp(bar.currentHeight, targetH, lerpSpeed);
    bar.mesh.scale.set(1.0, bar.currentHeight, 1.0);

    // Position top peak cap indicator
    if (bar.capMesh) {
      bar.capMesh.position.y = 1.0; // Fixed relative to scaled bar top
    }
  }

  // Smooth rotation of equalizer ring
  equalizerGroup.rotation.y += 0.12 * deltaTime;
}

/**
 * Updates color theme of 3D Equalizer Ring dynamically based on active emotion state.
 * 
 * @param {THREE.Group} equalizerGroup 
 * @param {number|string|THREE.Color} colorVal 
 */
export function setSpectrumColor(equalizerGroup, colorVal) {
  if (!equalizerGroup || !equalizerGroup.userData || !equalizerGroup.userData.bars) return;

  const baseColor = new THREE.Color(colorVal);
  const { bars, barCount } = equalizerGroup.userData;

  bars.forEach((bar, i) => {
    // Generate harmonious hue gradient offset around ring
    const hueOffset = (i / barCount) * 0.28;
    const barColor = baseColor.clone().offsetHSL(hueOffset, 0, 0);

    if (bar.material) {
      bar.material.color.lerp(barColor, 0.25);
    }

    if (bar.capMaterial) {
      const capColor = barColor.clone().addScalar(0.4);
      bar.capMaterial.color.lerp(capColor, 0.25);
    }
  });

  if (equalizerGroup.userData.ringMesh && equalizerGroup.userData.ringMesh.material) {
    equalizerGroup.userData.ringMesh.material.color.lerp(baseColor, 0.25);
  }
}




