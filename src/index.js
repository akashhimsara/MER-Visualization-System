import { Engine } from './visual-engine/Engine.js';
import { EMOTION_PRESETS, EMOTION_VA_PRESETS } from './visuals/emotions.js';
import { DEFAULT_VISUAL_PARAMS, VISUAL_PROFILES } from './visuals/parameters.js';
import { createDebugPanel } from './ui/debug-panel.js';
import { triggerBeatPulse } from './visuals/beat.js';
import { VISUAL_MODES } from './visuals/modes.js';

/**
 * Public Facade API for the AI-Assisted Emotion-Aware Visualization Engine.
 * Serves as the primary integration entry point for team members & external modules.
 */
export class VisualizationEngine {
  /**
   * Initializes the Visualization Engine on a target DOM container.
   * @param {HTMLElement} containerElement - DOM node to attach WebGL Canvas
   * @param {boolean} showDebugControls - If true, mounts the interactive developer debug HUD
   */
  constructor(containerElement, showDebugControls = true) {
    if (!containerElement) {
      throw new Error('[VisualizationEngine] A valid DOM container element is required.');
    }
    this.engine = new Engine(containerElement);

    if (showDebugControls) {
      createDebugPanel(this);
    }
  }

  /**
   * Starts the 60 FPS Three.js rendering and animation loop.
   */
  start() {
    this.engine.start();
  }

  /**
   * Stops the render loop and disposes WebGL resources cleanly.
   */
  stop() {
    this.engine.destroy();
  }

  /**
   * Triggers an immediate audio-reactive beat kick pulse (scales particles, mesh, and light flash).
   * @param {number} intensity - Pulse intensity scalar (0.0 to 1.0)
   */
  triggerBeat(intensity = 1.0) {
    this.engine.triggerBeat(intensity);
  }

  /**
   * Triggers a smooth, timed transition to a target emotion state ('CALM', 'HAPPY', 'ENERGETIC', 'SAD').
   * 
   * @param {string} emotionName - High-level emotion state key
   * @param {number} durationSeconds - Transition duration in seconds (default: 2.0s)
   */
  setEmotion(emotionName, durationSeconds = 2.0) {
    this.engine.transitionToEmotion(emotionName, durationSeconds);
  }

  /**
   * Sets active 3D Visualizer Mode ('EQUALIZER_RING' | 'NEON_TUNNEL' | 'HOLOGRAPHIC_CORE' | 'HORIZON_GRID').
   * @param {string} modeKey 
   */
  setVisualMode(modeKey) {
    this.engine.setVisualMode(modeKey);
  }

  /**
   * Sets continuous Valence-Arousal AI emotion coordinates (-1.0 to 1.0)
   * and maps them dynamically to visual parameters using Russell's Circumplex Model.
   * 
   * @param {number} valence - Positivity (-1.0 to 1.0)
   * @param {number} arousal - Energy (-1.0 to 1.0)
   */
  setValenceArousal(valence = 0.0, arousal = 0.0) {
    return this.engine.setValenceArousal(valence, arousal);
  }

  /**
   * Dynamically updates custom visual parameters (particleColor, motionSpeed, motionIntensity, lightColor, lightIntensity).
   * 
   * @param {object} parametersBundle - Object containing parameter overrides
   * @param {boolean} smoothTransition - If true, lerps color values smoothly
   */
  updateParameters(parametersBundle, smoothTransition = true) {
    this.engine.updateVisualParameters(parametersBundle, smoothTransition);
  }

  /**
   * Returns list of supported emotion keys.
   * @returns {string[]}
   */
  getSupportedEmotions() {
    return Object.keys(EMOTION_PRESETS);
  }

  /**
   * Returns current active transition parameters.
   * @returns {object}
   */
  getTransitionState() {
    return this.engine.transitionController ? this.engine.transitionController.currentParams : null;
  }
}

// Export visual preset constants & helper modules
export { EMOTION_PRESETS, EMOTION_VA_PRESETS, VISUAL_PROFILES, DEFAULT_VISUAL_PARAMS, createDebugPanel, triggerBeatPulse, VISUAL_MODES };
