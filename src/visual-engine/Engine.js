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
import { createVisualChapterController, updateVisualChapter } from '../audio/visual-chapters.js';
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
    this.visualChapterController = createVisualChapterController();
    this.visualChapter = { key: 'DORMANT', intensity: 0 };
    this.songOutroTriggered = false;

    // Initialize AI Mapping Model
    this.aiModel = new EmotionAIModel();
    this.songVisualDNA = null;
    this.pendingSongFile = null;
    this.isVisualReady = false;
    this.lockedVisualFamily = null;
    // During the Rose polish phase, every demo song opens the same hero
    // family. This makes visual QA repeatable; Song DNA still varies palette,
    // seed and motion. Remove this override once all four families are ready.
    this.visualPreviewFamily = VISUAL_MODES.COSMIC_BLOOM;
    this.lastAudioProfileKey = 'ANALYZING';
    this.currentPrediction = null;
    this.lastAudioHudUpdate = -Infinity;

    // Emotion Settings
    this.emotionKeys = Object.keys(EMOTION_PRESETS);
    this.lastTriggeredEmotionIndex = -1;
    this.emotionCycleInterval = 6.0;
    this.autoEmotionCycle = true; // Set to false when user manually selects an emotion!

    // Apply the same trained-model input path used by the named emotion controls.
    this.setValenceArousal(EMOTION_VA_PRESETS.CALM.valence, EMOTION_VA_PRESETS.CALM.arousal, false);

    // Mount canvas to DOM container
    this.container.appendChild(this.renderer.domElement);
    this.hideVisualForSetup();

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
      this.autoEmotionCycle = false;
      this.modeManager.switchMode(modeKey);
      this.modeManager.startModeIntro(modeKey, this.getStoryTime());
      if (this.particles) this.particles.visible = ![VISUAL_MODES.COSMIC_IRIS, VISUAL_MODES.LIQUID_CHROME_GALAXY, VISUAL_MODES.COSMIC_BLOOM].includes(modeKey);
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
    this.songOutroTriggered = false;
    this.pendingSongFile = file;
    this.songVisualDNA = null;
    this.lockedVisualFamily = this.visualPreviewFamily;
    this.hideVisualForSetup();
    return null;
  }

  /** Keep the stage intentionally empty until a song and sample emotion are chosen. */
  hideVisualForSetup() {
    this.isVisualReady = false;
    if (this.modeManager?.modes) {
      Object.values(this.modeManager.modes).forEach((group) => { group.visible = false; });
    }
    if (this.particles) this.particles.visible = false;
    if (this.placeholderMesh) this.placeholderMesh.visible = false;
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
    this.songVisualDNA = createSongVisualDNA(fingerprint, prediction.predictedCategory, prediction.particleColor, audioProfile, this.lockedVisualFamily);
    this.lockedVisualFamily ||= this.songVisualDNA.visualMode;
    this.applySongVisualDNA();
    return this.songVisualDNA;
  }

  applySongVisualDNA() {
    if (!this.songVisualDNA || !this.modeManager) return null;
    const { palette, variation, visualMode } = this.songVisualDNA;
    this.modeManager.switchMode(visualMode);
    this.isVisualReady = true;
    if (this.audioAnalyzer?.isPlaying) this.modeManager.startModeIntro(visualMode, this.getStoryTime());
    else this.modeManager.armModeIntro(visualMode);
    if (this.particles) this.particles.visible = ![VISUAL_MODES.COSMIC_IRIS, VISUAL_MODES.LIQUID_CHROME_GALAXY, VISUAL_MODES.COSMIC_BLOOM].includes(visualMode);
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
      // Start a story only from the beginning of a track. Resume must preserve
      // the exact point in the visual narrative instead of replaying the intro.
      if ((this.audioAnalyzer.audioElement?.currentTime || 0) < 0.15) {
        this.modeManager?.startModeIntro(this.modeManager.activeMode, this.getStoryTime());
      }
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

  /** The story timeline is tied to the music, so pause/resume never desynchronises it. */
  getStoryTime() {
    return this.audioAnalyzer?.audioElement?.currentTime ?? this.clock.getElapsedTime();
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
    const prediction = this.setValenceArousal(vaPreset.valence, vaPreset.arousal, userInitiated);
    if (this.pendingSongFile) this.createSongVisualDNA(this.pendingSongFile);
    return prediction;
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
        this.songVisualDNA.audioProfile,
        this.lockedVisualFamily
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
      const isPortal = this.modeManager?.activeMode === VISUAL_MODES.COSMIC_IRIS;
      const isRose = this.modeManager?.activeMode === VISUAL_MODES.COSMIC_BLOOM;
      const portalSurge = this.visualChapter?.key === 'SURGE' ? 1 : 0;
      const beatPulse = this.beatController?.pulse || 0;
      const roseStoryTime = this.getStoryTime();
      const roseGrowth = THREE.MathUtils.smoothstep(8, 46, roseStoryTime);
      const roseSurge = this.visualChapter?.key === 'SURGE' ? 1 : 0;
      const targetX = isRose
        ? Math.sin(elapsedTime * .12) * (.18 + roseGrowth * .34) + Math.sin(elapsedTime * .46) * beatPulse * .075
        : isPortal ? 0 : Math.sin(elapsedTime * camOrbitSpeed) * camRadius;
      const targetZ = isRose
        ? 10.9 - roseGrowth * 2.0 - beatPulse * .22 - roseSurge * .42
        : isPortal ? 10 - beatPulse * 0.42 - portalSurge * 0.28 : Math.cos(elapsedTime * camOrbitSpeed) * camRadius;
      const targetY = isRose
        ? 2.86 + Math.sin(elapsedTime * .17) * .10 + beatPulse * .035
        : isPortal ? 1.45 : 3.2 + Math.sin(elapsedTime * 0.15 * motionEnergy) * 0.4;
      this.camera.position.lerp(new THREE.Vector3(targetX, targetY, targetZ), Math.min(1, deltaTime * 4.5));
      // The rose camera begins wide for the garden establishing shot and
      // closes in gradually as the bloom grows; bass adds only a restrained
      // cinematic push, never a distracting shake.
      this.camera.lookAt(0, isRose ? .46 + roseGrowth * .60 : 1.6, 0);
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
      this.visualChapter = updateVisualChapter(this.visualChapterController, audioMetrics, elapsedTime, deltaTime);
      window.dispatchEvent(new CustomEvent('visualchapter', { detail: this.visualChapter }));
      if (elapsedTime - this.lastAudioHudUpdate >= 0.1) {
        this.lastAudioHudUpdate = elapsedTime;
        window.dispatchEvent(new CustomEvent('audioanalysis', {
          detail: {
            bass: audioMetrics.bass,
            mid: audioMetrics.mid,
            high: audioMetrics.high,
            isBeat: audioMetrics.isBeat,
            profile: audioMetrics.profile?.key || 'ANALYZING'
          }
        }));
      }
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
          profile,
          this.lockedVisualFamily
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
      this.visualChapter = updateVisualChapter(this.visualChapterController, null, elapsedTime, deltaTime);
      if (this.audioAnalyzer?.hasEnded && !this.songOutroTriggered) {
        this.songOutroTriggered = true;
        this.modeManager?.startModeOutro(this.modeManager.activeMode, this.getStoryTime());
      }
      // Smoothly return particle size to baseline when audio stops
      if (this.particles && this.particles.material) {
        const baseSize = this.particles.userData?.baseSize || 0.45;
        this.particles.material.size = THREE.MathUtils.lerp(this.particles.material.size, baseSize, deltaTime * 5.0);
      }
    }

    // Update 3D Visual Geometry Modes with real audio frequency & beat pulse
    if (this.modeManager) {
      this.modeManager.update(freqData, deltaTime, elapsedTime, this.beatController?.pulse || 0.0, this.visualChapter, this.getStoryTime());
    }

    // This world is a focused energy system, not a tinted generic scene.
    // Keep its negative space dark even when the VA mapper updates global colours.
    if (this.modeManager?.activeMode === VISUAL_MODES.LIQUID_CHROME_GALAXY) {
      this.scene.background.set(0x020306);
    }

    // The Rose story needs cinematic negative space; its fog and moonlight
    // provide the colour, rather than a washed-out global scene background.
    if (this.modeManager?.activeMode === VISUAL_MODES.COSMIC_BLOOM) {
      const roseSky = {
        HAPPY: 0x1b5079,     // clean daylight-blue sky, not a starry night
        CALM: 0x06152c,
        SAD: 0x0b1728,
        ENERGETIC: 0x190c32
      }[this.currentPrediction?.predictedCategory] ?? 0x02040d;
      this.scene.background.set(roseSky);
    }

    if (this.bloomPass && this.modeManager?.activeMode === VISUAL_MODES.COSMIC_IRIS) {
      const surge = this.visualChapter?.key === 'SURGE' ? 0.34 : 0;
      const targetBloom = 0.72 + surge + (this.beatController?.pulse || 0) * 0.38;
      this.bloomPass.strength = THREE.MathUtils.lerp(this.bloomPass.strength, targetBloom, deltaTime * 4.5);
    }

    // Layered rose petals need colour separation more than maximum bloom.
    if (this.bloomPass && this.modeManager?.activeMode === VISUAL_MODES.COSMIC_BLOOM) {
      const targetBloom = 0.10 + (this.visualChapter?.key === 'SURGE' ? 0.07 : 0) + (this.beatController?.pulse || 0) * 0.05;
      this.bloomPass.strength = THREE.MathUtils.lerp(this.bloomPass.strength, targetBloom, deltaTime * 4.0);
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
