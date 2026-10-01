import * as THREE from 'three';

/**
 * Default lighting parameters.
 */
export const DEFAULT_LIGHTING = {
  ambientIntensity: 0.35,
  pointIntensity: 2.2,
  pointColor: 0x00f3ff
};

/**
 * Creates studio 3-point lighting (Ambient, Key Light, Rim Light) for Concept A Liquid Sphere.
 * @param {THREE.Scene} scene - The target Three.js scene
 * @returns {object} Lighting container holding light references and metadata
 */
export function createLighting(scene) {
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambientLight);

  // Central Equalizer Ring Light
  const pointLight = new THREE.PointLight(
    DEFAULT_LIGHTING.pointColor,
    1.5,
    30
  );
  pointLight.position.set(0, 1.8, 0);
  scene.add(pointLight);

  // Studio Key Light
  const keyLight = new THREE.PointLight(0x00f3ff, 1.8, 35);
  keyLight.position.set(4.0, 5.0, 4.0);
  scene.add(keyLight);

  // Studio Fill Light
  const fillLight = new THREE.PointLight(0xff00aa, 1.5, 30);
  fillLight.position.set(-4.0, 3.0, -3.0);
  scene.add(fillLight);

  const lighting = {
    ambientLight,
    pointLight,
    keyLight,
    fillLight,
    baseAmbientIntensity: 0.4,
    basePointIntensity: 1.5
  };

  return lighting;
}

/**
 * Sets light intensity dynamically.
 * @param {object} lighting - Lighting container object
 * @param {number} intensityMultiplier - Intensity scalar
 */
export function setLightIntensity(lighting, intensityMultiplier = 1.0) {
  if (!lighting) return;

  if (lighting.ambientLight) {
    lighting.ambientLight.intensity = DEFAULT_LIGHTING.ambientIntensity * intensityMultiplier;
  }
  if (lighting.pointLight) {
    lighting.pointLight.intensity = DEFAULT_LIGHTING.pointIntensity * intensityMultiplier;
  }
}

/**
 * Sets point light color dynamically.
 * Accepts hex values (0xff0077), hex strings ('#ff0077'), or THREE.Color instances.
 * 
 * @param {object} lighting - Lighting container object
 * @param {number|string|THREE.Color} colorValue - New light color
 */
export function setLightColor(lighting, colorValue) {
  if (!lighting || !lighting.pointLight) return;

  if (colorValue instanceof THREE.Color) {
    lighting.pointLight.color.copy(colorValue);
  } else {
    lighting.pointLight.color.set(colorValue);
  }

  if (lighting.rimLight) {
    const rimColor = new THREE.Color(colorValue).offsetHSL(0.4, 0, 0);
    lighting.rimLight.color.copy(rimColor);
  }
}

/**
 * Updates dynamic studio light motion on every frame.
 * @param {object} lighting - Lighting container object
 * @param {number} elapsedTime - Total elapsed time in seconds
 */
export function updateLighting(lighting, elapsedTime = 0) {
  if (!lighting || !lighting.pointLight) return;

  // Smooth orbital studio key light movement
  lighting.pointLight.position.x = Math.sin(elapsedTime * 0.6) * 4.5;
  lighting.pointLight.position.y = 3.0 + Math.cos(elapsedTime * 0.4) * 1.5;
  lighting.pointLight.position.z = 2.5 + Math.cos(elapsedTime * 0.6) * 2.0;

  if (lighting.rimLight) {
    lighting.rimLight.position.x = -Math.sin(elapsedTime * 0.5) * 4.0;
    lighting.rimLight.position.z = -2.5 - Math.cos(elapsedTime * 0.5) * 1.5;
  }
}

