import * as THREE from 'three';
import { createScene } from './scene.js';
import { createCamera, updateCameraAspect } from './camera.js';
import { createRenderer, createComposer, updateRendererSize } from './renderer.js';
import { createParticles, updateParticles, disposeParticles } from '../visuals/particles.js';
import { createLighting, updateLighting } from '../visuals/lighting.js';
import { applyVisualParameters, DEFAULT_VISUAL_PARAMS } from '../visuals/parameters.js';
import { EMOTION_PRESETS, setEmotionState } from '../visuals/emotions.js';
import { createBeatController, triggerBeatPulse, updateBeatReactor } from '../visuals/beat.js';
import { AudioAnalyzer } from '../audio/audio-analyzer.js';
import { EmotionVisualMapper } from '../ai/mapping-schema.js';
import { EmotionAIModel } from '../ai/emotion-ai-model.js';
import { updateSpectrumRing } from '../visuals/spectrum.js';

/**
 * Engine manages the Three.js lifecycle: scene creation, camera setup, 
 * rendering, window resizing, particles, color, motion, lighting, emotion states,
 * audio reactivity, and real audio file analysis.
 */
export class Engine {
  constructor(containerElement) {
    this.container = containerElement;
    this.animationFrameId = null;

    // Viewport dimensions
    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;

    // Core Three.js components
    const { scene, placeholderMesh, spectrumRing, bgFlareSprite } = createScene();
    this.scene = scene;
    this.placeholderMesh = placeholderMesh;
    this.spectrumRing = spectrumRing;
    this.bgFlareSprite = bgFlareSprite;

    this.camera = createCamera(this.width, this.height);
    this.renderer = createRenderer(this.width, this.height);

    // Initialize Post-Processing EffectComposer with UnrealBloomPass
    const { composer, bloomPass } = createComposer(this.renderer, this.scene, this.camera, this.width, this.height);
    this.composer = composer;
    this.bloomPass = bloomPass;

    // Initialize Scene Lighting
    this.lighting = createLighting(this.scene);

    // Clock for timing & delta calculation
    this.clock = new THREE.Clock();

    // Initialize Particle System (Speed particles)
    this.particles = createParticles(400, DEFAULT_VISUAL_PARAMS.particleColor);
    this.scene.add(this.particles);

    // Initialize EDM Beat Reactor Controller
    this.beatController = createBeatController();

    // Initialize Real Audio Analyzer
    this.audioAnalyzer = new AudioAnalyzer();

    // Initialize AI Mapping Model
    this.aiModel = new EmotionAIModel();

    // Emotion Settings
    this.emotionKeys = Object.keys(EMOTION_PRESETS);
    this.lastTriggeredEmotionIndex = -1;
    this.emotionCycleInterval = 6.0;
    this.autoEmotionCycle = true; // Set to false when user manually selects an emotion!

    // Apply initial CALM state
    setEmotionState(this.getEngineState(), 'CALM');

    // Mount canvas to DOM container
    this.container.appendChild(this.renderer.domElement);

    // Bind event handlers
    this.onWindowResize = this.onWindowResize.bind(this);
    this.loop = this.loop.bind(this);

    window.addEventListener('resize', this.onWindowResize);
  }

  /**
   * Helper to return current engine state targets bundle.
   */
  getEngineState() {
    return {
      scene: this.scene,
      camera: this.camera,
      placeholderMesh: this.placeholderMesh,
      spectrumRing: this.spectrumRing,
      bgFlareSprite: this.bgFlareSprite,
      particles: this.particles,
      lighting: this.lighting,
      bloomPass: this.bloomPass
    };
  }

  /**
   * Connects an HTML Audio Element to the Real-Time Audio Analyzer.
   * @param {HTMLAudioElement} audioElement 
   */
  connectAudioElement(audioElement) {
    if (this.audioAnalyzer) {
      this.audioAnalyzer.init(audioElement);
      this.beatController.autoBeatEnabled = false;
    }
  }

  /**
   * Loads a user-uploaded MP3/Audio File.
   * @param {File} file 
   */
  loadAudioFile(file) {
    if (this.audioAnalyzer) {
      this.audioAnalyzer.loadAudioFile(file);
    }
  }

  /**
   * Plays connected audio.
   */
  async playAudio() {
    if (this.audioAnalyzer) {
      await this.audioAnalyzer.play();
    }
  }

  /**
   * Pauses connected audio.
   */
  pauseAudio() {
    if (this.audioAnalyzer) {
      this.audioAnalyzer.pause();
    }
  }

  /**
   * Triggers a manual beat kick pulse (audio-reactive hit).
   * @param {number} intensity - Intensity scalar (0.0 to 1.0)
   */
  triggerBeat(intensity = 1.0) {
    triggerBeatPulse(this.beatController, intensity);
  }

  /**
   * Sets the active emotion state directly and locks user selection.
   * 
   * @param {string} emotionName - 'CALM' | 'HAPPY' | 'ENERGETIC' | 'SAD'
   * @param {number} durationSeconds - Optional transition parameter
   * @param {boolean} userInitiated - If true, locks in selected emotion
   */
  transitionToEmotion(emotionName, durationSeconds = 1.5, userInitiated = true) {
    if (userInitiated) {
      this.autoEmotionCycle = false; // Lock user selected emotion
    }
    setEmotionState(this.getEngineState(), emotionName);
  }

  /**
   * Directly set custom visual parameters.
   * @param {object} params 
   */
  updateVisualParameters(params) {
    applyVisualParameters(this.getEngineState(), params);
  }

  /**
   * Sets continuous Valence-Arousal AI emotion input coordinates (-1.0 to 1.0)
   * and uses the AI Mapping Model to predict dynamic 3D visual parameters.
   * 
   * @param {number} valence - Positivity (-1.0 to 1.0)
   * @param {number} arousal - Energy (-1.0 to 1.0)
   * @returns {object} Predicted visual parameters vector
   */
  setValenceArousal(valence = 0.0, arousal = 0.0) {
    this.autoEmotionCycle = false; // Lock user AI slider control
    const predictedParams = this.aiModel ? this.aiModel.predict(valence, arousal) : EmotionVisualMapper.mapValenceArousalToVisuals(valence, arousal);
    this.updateVisualParameters(predictedParams);
    return predictedParams;
  }

  /**
   * Main render loop called on every animation frame.
   */
  loop() {
    this.animationFrameId = requestAnimationFrame(this.loop);

    const elapsedTime = this.clock.getElapsedTime();
    const deltaTime = this.clock.getDelta();

    // Central Core Emblem & Dual Counter-Rotating Orbital Rings
    if (this.placeholderMesh) {
      this.placeholderMesh.position.y = Math.sin(elapsedTime * 0.8) * 0.08;
      const ringA = this.placeholderMesh.getObjectByName('wireframeLines');
      const ringB = this.placeholderMesh.getObjectByName('orbitalRingB');
      if (ringA) ringA.rotation.y = elapsedTime * 0.45;
      if (ringB) {
        ringB.rotation.y = -elapsedTime * 0.35;
        ringB.rotation.x = elapsedTime * 0.25;
      }
    }

    // Update dynamic light positioning
    if (this.lighting) {
      updateLighting(this.lighting, elapsedTime);
    }

    // Auto-cycle emotions only if user hasn't manually selected one
    if (this.autoEmotionCycle) {
      const currentEmotionIndex = Math.floor(elapsedTime / this.emotionCycleInterval) % this.emotionKeys.length;
      if (currentEmotionIndex !== this.lastTriggeredEmotionIndex) {
        this.lastTriggeredEmotionIndex = currentEmotionIndex;
        const targetEmotionKey = this.emotionKeys[currentEmotionIndex];
        this.transitionToEmotion(targetEmotionKey, 1.5, false);
      }
    }

    // Analyze Real Audio Frequencies (if audio is playing)
    if (this.audioAnalyzer && this.audioAnalyzer.isPlaying) {
      const audioMetrics = this.audioAnalyzer.update(elapsedTime);
      
      // 1. Bass Frequency (Kick Drums): Trigger physical beat pulse
      if (audioMetrics.isBeat) {
        this.triggerBeat(Math.min(1.0, audioMetrics.bass * 1.5));
      }

      // 2. Mid Frequency (Synths / Vocals): Modulate wave turbulence and spin acceleration
      if (this.particles && this.particles.userData) {
        const midBoost = audioMetrics.mid * 0.03;
        this.particles.rotation.z += midBoost;
        this.particles.rotation.x += midBoost * 0.5;
      }

      // 3. High Frequency (Hi-Hats / Snares): Modulate particle point size for shimmer/twinkle effect
      if (this.particles && this.particles.material) {
        const baseSize = this.particles.userData?.baseSize || 0.45;
        const targetSize = baseSize + (audioMetrics.high * 0.25);
        this.particles.material.size = THREE.MathUtils.lerp(this.particles.material.size, targetSize, deltaTime * 10.0);
      }
    } else {
      // Smoothly return particle size to baseline when audio stops
      if (this.particles && this.particles.material) {
        const baseSize = this.particles.userData?.baseSize || 0.45;
        this.particles.material.size = THREE.MathUtils.lerp(this.particles.material.size, baseSize, deltaTime * 5.0);
      }
    }

    // Real-Time 3D Audio Frequency Waveform Spectrum Line Ring Update
    if (this.spectrumRing) {
      const freqData = (this.audioAnalyzer && this.audioAnalyzer.isPlaying && this.audioAnalyzer.frequencyData) ? this.audioAnalyzer.frequencyData : null;
      updateSpectrumRing(this.spectrumRing, freqData, deltaTime, elapsedTime, this.beatController?.pulse || 0.0);
    }

    // Update audio-reactive EDM beat pulse reaction
    updateBeatReactor(this.beatController, this.getEngineState(), elapsedTime, deltaTime);

    // Update particle motion & frame geometry
    if (this.particles) {
      updateParticles(this.particles, elapsedTime, deltaTime);
    }

    // Render using EffectComposer for Neon Bloom
    if (this.composer) {
      this.composer.render();
    } else {
      this.renderer.render(this.scene, this.camera);
    }
  }

  /**
   * Handle responsive resize of canvas and camera projection matrix.
   */
  onWindowResize() {
    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;

    updateCameraAspect(this.camera, this.width, this.height);
    updateRendererSize(this.renderer, this.width, this.height, this.composer);
  }

  /**
   * Start the animation loop.
   */
  start() {
    if (!this.animationFrameId) {
      this.clock.start();
      this.loop();
    }
  }

  /**
   * Stop the animation loop and clean up resources.
   */
  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    window.removeEventListener('resize', this.onWindowResize);

    // Dispose particle system
    if (this.particles) {
      this.scene.remove(this.particles);
      disposeParticles(this.particles);
      this.particles = null;
    }

    if (this.renderer.domElement && this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
    this.renderer.dispose();
  }
}
