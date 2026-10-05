import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

/**
 * Creates and configures the WebGL Renderer with ReinhardToneMapping.
 * @param {number} width - Viewport width
 * @param {number} height - Viewport height
 * @returns {THREE.WebGLRenderer}
 */
export function createRenderer(width, height) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ReinhardToneMapping;
  renderer.toneMappingExposure = 1.2;
  return renderer;
}

/**
 * Creates an EffectComposer with UnrealBloomPass tuned for ultra-clean pin-sharp modern glow.
 * @param {THREE.WebGLRenderer} renderer 
 * @param {THREE.Scene} scene 
 * @param {THREE.PerspectiveCamera} camera 
 * @param {number} width 
 * @param {number} height 
 * @returns {{ composer: EffectComposer, bloomPass: UnrealBloomPass }}
 */
export function createComposer(renderer, scene, camera, width, height) {
  const composer = new EffectComposer(renderer);
  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  // Pin-sharp crisp neon bloom pass (prevents white blowout while preserving vibrant neon glow)
  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(width, height),
    0.35,  // Crisp bloom strength
    0.25,  // Controlled glow radius
    0.55   // High threshold prevents solid white/yellow over-exposure
  );
  composer.addPass(bloomPass);

  return { composer, bloomPass };
}

/**
 * Updates renderer and composer dimensions on window resize.
 * @param {THREE.WebGLRenderer} renderer 
 * @param {number} width 
 * @param {number} height 
 * @param {EffectComposer|null} composer
 */
export function updateRendererSize(renderer, width, height, composer = null) {
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  if (composer) {
    composer.setSize(width, height);
  }
}
