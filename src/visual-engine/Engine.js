import * as THREE from 'three';
import { createScene } from './scene.js';
import { createCamera, updateCameraAspect } from './camera.js';
import { createRenderer, createComposer, updateRendererSize } from './renderer.js';
import { createParticles, updateParticles, disposeParticles, setParticleDensity } from '../visuals/particles.js';
import { createLighting, updateLighting } from '../visuals/lighting.js';
import { applyVisualParameters, DEFAULT_VISUAL_PARAMS } from '../visuals/parameters.js';
import { EMOTION_PRESETS, EMOTION_VA_PRESETS } from '../visuals/emotions.js';
import { createBeatController, triggerBeatPulse, updateBeatReactor } from '../visuals/beat.js';
import { AudioAnalyzer } from '../audio/audio-analyzer.js';
import { EmotionVisualMapper } from '../ai/mapping-schema.js';
import { EmotionAIModel } from '../ai/emotion-ai-model.js';
import { createSongVisualDNA, fingerprintSong } from '../ai/song-visual-dna.js';
import { VisualModeManager, VISUAL_MODES } from '../visuals/modes.js';

/**
 * Engine manages the Three.js lifecycle: scene creation, camera setup, 
 * rendering, window resizing, particles, color, motion, lighting, emotion states,
 * audio reactivity, multi-mode 3D geometry morphing, and real audio file analysis.
 */
export class Engine {
  constructor(containerElement) {
    this.container = containerElement;
    this.animationFrameId = null;

    // Viewport dimensions
    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;

    // Core Three.js components
    const { scene, placeholderMesh, bgFlareSprite } = createScene();
    this.scene = scene;
    this.placeholderMesh = placeholderMesh;
    this.bgFlareSprite = bgFlareSprite;

    // Initialize Multi-Mode 3D Geometry Manager (Equalizer, Tunnel, Crystal Core, Horizon Grid)
    this.modeManager = new VisualModeManager(this.scene);
    this.spectrumRing = this.modeManager.modes[VISUAL_MODES.EQUALIZER_RING];

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
    this.particles = createParticles(1000, DEFAULT_VISUAL_PARAMS.particleColor);
    setParticleDensity(this.particles, 400);
    this.scene.add(this.particles);

    // Initialize EDM Beat Reactor Controller
    this.beatController = createBeatController();

    // Initialize Real Audio Analyzer
    this.audioAnalyzer = new AudioAnalyzer();

    // Initialize AI Mapping Model
    this.aiModel = new EmotionAIModel();
    this.songVisualDNA = null;
    this.lastAudioProfileKey = 'ANALYZING';
    this.currentPrediction = null;

    // Emotion Settings
    this.emotionKeys = Object.keys(EMOTION_PRESETS);
    this.lastTriggeredEmotionIndex = -1;
    this.emotionCycleInterval = 6.0;
    this.autoEmotionCycle = true; // Set to false when user manually selects an emotion!

    // Apply the same trained-model input path used by the named emotion controls.
    this.setValenceArousal(EMOTION_VA_PRESETS.CALM.valence, EMOTION_VA_PRESETS.CALM.arousal, false);

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
      modeManager: this.modeManager,
      spectrumRing: this.spectrumRing,
      bgFlareSprite: this.bgFlareSprite,
      particles: this.particles,
      lighting: this.lighting,
      bloomPass: this.bloomPass
    };
  }

  /**
   * Directly sets active 3D Visualizer Mode ('EQUALIZER_RING' | 'NEON_TUNNEL' | 'HOLOGRAPHIC_CORE' | 'HORIZON_GRID').
   * @param {string} modeKey 
   */
  setVisualMode(modeKey) {
    if (this.modeManager) {
      this.modeManager.switchMode(modeKey);
    }
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
    // A real song must not be overwritten by the no-audio demo emotion cycle.
    this.autoEmotionCycle = false;
    return this.createSongVisualDNA(file);
  }

  /**
   * Creates and applies a deterministic visual identity for an uploaded song.
   * This is a variation layer, separate from the trained VA-to-parameters
   * mapping model.
   */
  createSongVisualDNA(file) {
    const prediction = this.currentPrediction || this.aiModel.predict(0.60, -0.50);
    const fingerprint = fingerprintSong(file);
    const audioProfile = this.audioAnalyzer?.getAudioProfile() || { key: 'ANALYZING' };
    this.lastAudioProfileKey = audioProfile.key;
    this.songVisualDNA = createSongVisualDNA(fingerprint, prediction.predictedCategory, prediction.particleColor, audioProfile);
    this.applySongVisualDNA();
    return this.songVisualDNA;
  }

  applySongVisualDNA() {
    if (!this.songVisualDNA || !this.modeManager) return null;
    const { palette, variation, visualMode } = this.songVisualDNA;
    this.modeManager.switchMode(visualMode);
    this.modeManager.setModeFromEmotion(this.songVisualDNA.emotionCategory, palette.primary, palette.secondary);
    window.dispatchEvent(new CustomEvent('songvisualdna', { detail: this.songVisualDNA }));
    return this.songVisualDNA;
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
   * The named emotion is converted to its canonical VA input, then passed to
   * the trained visual-mapping model. It does not bypass AI inference.
   * 
   * @param {string} emotionName - 'CALM' | 'HAPPY' | 'ENERGETIC' | 'SAD'
   * @param {number} durationSeconds - Optional transition parameter
   * @param {boolean} userInitiated - If true, locks in selected emotion
   */
  transitionToEmotion(emotionName, durationSeconds = 1.5, userInitiated = true) {
    if (userInitiated) {
      this.autoEmotionCycle = false; // Lock user selected emotion
    }
    const key = String(emotionName).toUpperCase();
    const vaPreset = EMOTION_VA_PRESETS[key] || EMOTION_VA_PRESETS.CALM;
    return this.setValenceArousal(vaPreset.valence, vaPreset.arousal, userInitiated);
  }

  /**
   * Directly set custom visual parameters.
   * @param {object} params 
   */
  updateVisualParameters(params) {
    return applyVisualParameters(this.getEngineState(), params);
  }

  /**
   * Sets continuous Valence-Arousal AI emotion input coordinates (-1.0 to 1.0)
   * and uses the AI Mapping Model to predict dynamic 3D visual parameters and 3D Visual Mode.
   * 
   * @param {number} valence - Positivity (-1.0 to 1.0)
   * @param {number} arousal - Energy (-1.0 to 1.0)
   * @returns {object} Predicted visual parameters vector
   */
  setValenceArousal(valence = 0.0, arousal = 0.0, userInitiated = true) {
    if (userInitiated) this.autoEmotionCycle = false; // Lock manual controls only
    const predictedParams = this.aiModel ? this.aiModel.predict(valence, arousal) : EmotionVisualMapper.mapValenceArousalToVisuals(valence, arousal);
    this.currentPrediction = predictedParams;
    this.updateVisualParameters(predictedParams);

    if (predictedParams && predictedParams.predictedCategory && this.modeManager) {
      this.modeManager.setModeFromEmotion(
        predictedParams.predictedCategory,
        predictedParams.particleColor,
        predictedParams.lightColor
      );
    }

    // Preserve song-specific identity while adapting its selected visual world
    // to the current emotion supplied by a slider or future MER integration.
    if (this.songVisualDNA) {
      this.songVisualDNA = createSongVisualDNA(
        this.songVisualDNA.songFingerprint,
        predictedParams.predictedCategory,
        predictedParams.particleColor,
        this.songVisualDNA.audioProfile
      );
      this.applySongVisualDNA();
    }

    return predictedParams;
  }

  /**
   * Main render loop called on every animation frame.
   */
  loop() {
    this.animationFrameId = requestAnimationFrame(this.loop);

    const elapsedTime = this.clock.getElapsedTime();
    const deltaTime = this.clock.getDelta();

    // Smooth Cinematic Slow Camera Orbit Motion
    if (this.camera) {
      const dnaVariation = this.songVisualDNA?.variation;
      const camRadius = dnaVariation?.cameraRadius || 9.0;
      const camOrbitSpeed = dnaVariation?.cameraOrbitSpeed || 0.08;
      const motionEnergy = dnaVariation?.visualEnergy || 1.0;
      this.camera.position.x = Math.sin(elapsedTime * camOrbitSpeed) * camRadius;
      this.camera.position.z = Math.cos(elapsedTime * camOrbitSpeed) * camRadius;
      this.camera.position.y = 3.2 + Math.sin(elapsedTime * 0.15 * motionEnergy) * 0.4;
      this.camera.lookAt(0, 1.6, 0);
    }

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
    let freqData = null;
    if (this.audioAnalyzer && this.audioAnalyzer.isPlaying) {
      const audioMetrics = this.audioAnalyzer.update(elapsedTime);
      freqData = this.audioAnalyzer.frequencyData;

      // After a short real-audio sample, upgrade the initial recipe using the
      // track's sound balance. This works for EDM and ordinary music alike.
      const profile = audioMetrics.profile;
      if (this.songVisualDNA && profile?.key && profile.key !== 'ANALYZING' && profile.key !== this.lastAudioProfileKey) {
        this.lastAudioProfileKey = profile.key;
        this.songVisualDNA = createSongVisualDNA(
          this.songVisualDNA.songFingerprint,
          this.currentPrediction?.predictedCategory,
          this.currentPrediction?.particleColor,
          profile
        );
        this.applySongVisualDNA();
      }
      
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

    // Update 3D Visual Geometry Modes with real audio frequency & beat pulse
    if (this.modeManager) {
      this.modeManager.update(freqData, deltaTime, elapsedTime, this.beatController?.pulse || 0.0);
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
