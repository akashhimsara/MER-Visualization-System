/**
 * Creates and mounts a translucent developer control overlay
 * with Real Audio File Upload, Audio Player Controls, Kick Beat Trigger,
 * and Emotion State Selectors.
 * 
 * @param {VisualizationEngine} engineInstance - Instance of VisualizationEngine
 */
export function createDebugPanel(engineInstance) {
  if (!engineInstance) return;

  // Create HTML Audio Element for playing uploaded music files
  const audioElement = document.createElement('audio');
  audioElement.id = 'viz-audio-player';
  audioElement.controls = false;
  document.body.appendChild(audioElement);

  // Connect Audio Element to Engine Audio Analyzer
  if (engineInstance.engine && engineInstance.engine.connectAudioElement) {
    engineInstance.engine.connectAudioElement(audioElement);
  }

  // Create panel container element
  const panel = document.createElement('div');
  panel.id = 'debug-panel';
  panel.style.position = 'fixed';
  panel.style.top = '20px';
  panel.style.right = '20px';
  panel.style.zIndex = '9999';
  panel.style.padding = '16px';
  panel.style.borderRadius = '12px';
  panel.style.background = 'rgba(15, 15, 25, 0.85)';
  panel.style.backdropFilter = 'blur(16px)';
  panel.style.webkitBackdropFilter = 'blur(16px)';
  panel.style.border = '1px solid rgba(255, 255, 255, 0.15)';
  panel.style.color = '#ffffff';
  panel.style.fontFamily = 'system-ui, -apple-system, sans-serif';
  panel.style.fontSize = '12px';
  panel.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.5)';
  panel.style.width = '240px';
  panel.style.transition = 'all 0.3s ease';

  // Title & Status HUD
  panel.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      <span style="font-weight: 700; letter-spacing: 0.5px; color: #00f3ff; font-size: 13px;">ENGINE CONTROLLER</span>
      <button id="toggle-panel-btn" style="background: none; border: none; color: #888; cursor: pointer; font-size: 14px;">✕</button>
    </div>
    
    <!-- Audio File Upload Section -->
    <div style="margin-bottom: 12px; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px dashed rgba(0,243,255,0.3);">
      <div style="font-weight: 600; color: #00f3ff; margin-bottom: 6px;">🎵 Real Audio Analyzer</div>
      <input type="file" id="audio-file-input" accept="audio/*" style="display: none;" />
      <button id="choose-audio-btn" style="width: 100%; padding: 6px 10px; margin-bottom: 6px; border-radius: 5px; border: 1px solid #00f3ff; background: rgba(0,243,255,0.15); color: #00f3ff; cursor: pointer; font-weight: 600;">📁 Upload MP3/Music File</button>
      <div id="audio-filename" style="font-size: 10px; color: #888; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; margin-bottom: 6px;">No audio file loaded</div>
      <div style="display: flex; gap: 6px;">
        <button id="play-audio-btn" style="flex: 1; padding: 6px; border-radius: 5px; border: 1px solid #00ffaa; background: rgba(0,255,170,0.15); color: #00ffaa; cursor: pointer; font-weight: 600;">▶ Play</button>
        <button id="pause-audio-btn" style="flex: 1; padding: 6px; border-radius: 5px; border: 1px solid #ffaa00; background: rgba(255,170,0,0.15); color: #ffaa00; cursor: pointer; font-weight: 600;">⏸ Pause</button>
      </div>
    </div>

    <!-- Status HUD -->
    <div id="status-hud" style="margin-bottom: 12px; font-size: 11px; color: #aaa; line-height: 1.5; padding: 6px 8px; background: rgba(0,0,0,0.2); border-radius: 6px;">
      <div>Active State: <span id="active-state-label" style="color: #00f3ff; font-weight: 700;">AUTO CYCLE</span></div>
      <div>Rendering: <span style="color: #00ffaa; font-weight: 600;">60 FPS (WebGL)</span></div>
    </div>

    <div style="margin-bottom: 12px; padding: 9px 10px; border-radius: 8px; background: rgba(111, 77, 255, 0.09); border: 1px solid rgba(157, 117, 255, 0.3);">
      <div style="display: flex; justify-content: space-between; gap: 8px; margin-bottom: 4px;">
        <span style="font-weight: 700; color: #c9b6ff;">SONG VISUAL DNA</span>
        <span style="font-size: 9px; color: #8f85a8;">UNIQUE RECIPE</span>
      </div>
      <div id="visual-dna-summary" aria-live="polite" style="font-size: 10px; color: #c8c8d4; line-height: 1.45;">Upload a song to generate its visual identity.</div>
    </div>

    <!-- AI Continuous Valence-Arousal Mapper Section -->
    <div style="margin-bottom: 12px; padding: 10px; border-radius: 8px; background: rgba(0, 243, 255, 0.05); border: 1px solid rgba(0, 243, 255, 0.2);">
      <div style="font-weight: 600; color: #00f3ff; margin-bottom: 8px; display: flex; justify-content: space-between;">
        <span>🧠 AI Emotion Mapper</span>
        <span style="font-size: 10px; color: #00ffaa;">2D Circumplex</span>
      </div>
      
      <!-- Valence Slider -->
      <div style="margin-bottom: 6px;">
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #ccc; margin-bottom: 2px;">
          <span>Valence (Positivity)</span>
          <span id="val-val-disp" style="color: #00f3ff; font-weight: 600;">0.00</span>
        </div>
        <input type="range" id="valence-slider" min="-1" max="1" step="0.05" value="0" style="width: 100%; cursor: pointer;" />
      </div>

      <!-- Arousal Slider -->
      <div>
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #ccc; margin-bottom: 2px;">
          <span>Arousal (Energy)</span>
          <span id="aro-val-disp" style="color: #ff0055; font-weight: 600;">0.00</span>
        </div>
        <input type="range" id="arousal-slider" min="-1" max="1" step="0.05" value="0" style="width: 100%; cursor: pointer;" />
      </div>
    </div>

    <!-- Read-only evidence of the trained model's live parameter prediction -->
    <div style="margin-bottom: 12px; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255, 0, 170, 0.25);">
      <div style="display: flex; justify-content: space-between; gap: 8px; margin-bottom: 6px;">
        <span style="font-weight: 700; color: #ff74bd;">MODEL OUTPUT</span>
        <span style="font-size: 9px; color: #00ffaa;">TRAINED BASELINE</span>
      </div>
      <div id="model-output-summary" aria-live="polite" style="font-size: 10px; color: #c8c8d4; line-height: 1.55;">Select an emotion or move the VA controls.</div>
    </div>

    <!-- 3D Geometry Mode Selector -->
    <div style="margin-bottom: 12px; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(0, 243, 255, 0.2);">
      <div style="font-weight: 600; color: #00f3ff; margin-bottom: 6px;">🎮 3D Visualizer Mode</div>
      <select id="visual-mode-select" style="width: 100%; padding: 6px; border-radius: 5px; border: 1px solid #00f3ff; background: rgba(0,243,255,0.1); color: #fff; cursor: pointer; font-weight: 600;">
        <option value="LIQUID_CHROME_GALAXY" style="background: #111; color: #00f3ff;">🌊 LIQUID CHROME GALAXY (Tomorrowland Master)</option>
        <option value="NEON_MANDALA" style="background: #111; color: #9efcff;">✦ NEON MANDALA (Procedural Art)</option>
        <option value="COSMIC_BLOOM" style="background: #111; color: #bfffe9;">✧ COSMIC BLOOM (Energy Tree)</option>
        <option value="PARTICLE_AURORA" style="background: #111; color: #8dfaff;">≈ PARTICLE AURORA (Flow Field)</option>
        <option value="VOID_PORTAL" style="background: #111; color: #ff8ed8;">◉ VOID PORTAL (Bass Vortex)</option>
        <option value="CRYSTAL_CATHEDRAL" style="background: #111; color: #c8faff;">CRYSTAL CATHEDRAL (Uplifting / Vocal)</option>
        <option value="SOLAR_ECLIPSE" style="background: #111; color: #ffd184;">SOLAR ECLIPSE (Cinematic / Emotional)</option>
        <option value="NEON_LOTUS" style="background: #111; color: #aaffee;">NEON LOTUS (Vocal / Acoustic)</option>
      </select>
    </div>

    <!-- Emotion Presets -->
    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #777; margin-bottom: 6px;">Select Emotion Preset</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 10px;">
      <button class="emotion-btn" data-emotion="CALM" style="padding: 7px; border-radius: 6px; border: 1px solid #00d4ff; background: rgba(0,212,255,0.12); color: #00d4ff; cursor: pointer; font-weight: 600;">CALM</button>
      <button class="emotion-btn" data-emotion="HAPPY" style="padding: 7px; border-radius: 6px; border: 1px solid #ffd700; background: rgba(255,215,0,0.12); color: #ffd700; cursor: pointer; font-weight: 600;">HAPPY</button>
      <button class="emotion-btn" data-emotion="ENERGETIC" style="padding: 7px; border-radius: 6px; border: 1px solid #ff0055; background: rgba(255,0,85,0.12); color: #ff0055; cursor: pointer; font-weight: 600;">ENERGETIC</button>
      <button class="emotion-btn" data-emotion="SAD" style="padding: 7px; border-radius: 6px; border: 1px solid #3d5a80; background: rgba(61,90,128,0.12); color: #8ab4f8; cursor: pointer; font-weight: 600;">SAD</button>
    </div>
    
    <div style="font-size: 10px; color: #555; text-align: center;">Press 'H' key to toggle HUD</div>
  `;

  document.body.appendChild(panel);

  // Audio File Upload Wire-up
  const fileInput = panel.querySelector('#audio-file-input');
  const chooseAudioBtn = panel.querySelector('#choose-audio-btn');
  const audioFilenameLabel = panel.querySelector('#audio-filename');
  const playBtn = panel.querySelector('#play-audio-btn');
  const pauseBtn = panel.querySelector('#pause-audio-btn');
  const visualDnaSummary = panel.querySelector('#visual-dna-summary');

  const renderVisualDNA = (recipe) => {
    if (!visualDnaSummary || !recipe) return;
    const primary = `#${recipe.palette.primary.toString(16).padStart(6, '0')}`.toUpperCase();
    panel.dataset.audioProfile = recipe.audioProfile?.key || 'ANALYZING';
    visualDnaSummary.textContent = `${recipe.visualMode.replaceAll('_', ' ')} · ${recipe.emotionCategory} · seed ${recipe.seed.toString(16).toUpperCase()} · ${primary}`;
  };

  chooseAudioBtn.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      audioFilenameLabel.textContent = file.name;
      if (engineInstance.engine && engineInstance.engine.loadAudioFile) {
        renderVisualDNA(engineInstance.engine.loadAudioFile(file));
      }
    }
  });

  playBtn.addEventListener('click', async () => {
    if (engineInstance.engine && engineInstance.engine.playAudio) {
      await engineInstance.engine.playAudio();
    }
  });

  pauseBtn.addEventListener('click', () => {
    if (engineInstance.engine && engineInstance.engine.pauseAudio) {
      engineInstance.engine.pauseAudio();
    }
  });

  // Wire AI Valence & Arousal Sliders
  const valSlider = panel.querySelector('#valence-slider');
  const aroSlider = panel.querySelector('#arousal-slider');
  const valDisp = panel.querySelector('#val-val-disp');
  const aroDisp = panel.querySelector('#aro-val-disp');
  const modelOutputSummary = panel.querySelector('#model-output-summary');

  const renderModelOutput = (prediction) => {
    if (!modelOutputSummary || !prediction) return;
    const colour = `#${prediction.particleColor.toString(16).padStart(6, '0')}`.toUpperCase();
    modelOutputSummary.textContent = `${prediction.predictedCategory} · ${prediction.particleDensity} particles · speed ${prediction.motionSpeed.toFixed(2)} · bloom ${prediction.bloomStrength.toFixed(2)} · ${colour}`;
  };

  const updateAISliders = () => {
    const v = parseFloat(valSlider.value);
    const a = parseFloat(aroSlider.value);
    valDisp.textContent = v.toFixed(2);
    aroDisp.textContent = a.toFixed(2);

    if (engineInstance.setValenceArousal) {
      renderModelOutput(engineInstance.setValenceArousal(v, a));
    }
    if (activeLabel) {
      activeLabel.textContent = `AI MAPPER (V:${v.toFixed(1)}, A:${a.toFixed(1)})`;
      activeLabel.style.color = '#00f3ff';
    }
  };

  if (valSlider && aroSlider) {
    valSlider.addEventListener('input', updateAISliders);
    aroSlider.addEventListener('input', updateAISliders);
  }

  // Wire 3D Visualizer Mode Select Dropdown
  const modeSelect = panel.querySelector('#visual-mode-select');

  window.addEventListener('songvisualdna', (event) => {
    const recipe = event.detail;
    renderVisualDNA(recipe);
    if (modeSelect && recipe?.visualMode) {
      modeSelect.value = recipe.visualMode;
    }
  });

  if (modeSelect) {
    modeSelect.addEventListener('change', (e) => {
      const selectedMode = e.target.value;
      if (engineInstance.setVisualMode) {
        engineInstance.setVisualMode(selectedMode);
      }
    });
  }

  // Wire Emotion Buttons
  const buttons = panel.querySelectorAll('.emotion-btn');
  const activeLabel = panel.querySelector('#active-state-label');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const emotion = btn.getAttribute('data-emotion');
      
      // Call setEmotion on Engine
      renderModelOutput(engineInstance.setEmotion(emotion, 2.0));
      
      if (activeLabel) {
        activeLabel.textContent = emotion + ' (LOCKED)';
        activeLabel.style.color = '#00ffaa';
      }

      // Highlight active button
      buttons.forEach(b => {
        b.style.opacity = '0.5';
        b.style.boxShadow = 'none';
      });
      btn.style.opacity = '1.0';
      btn.style.boxShadow = '0 0 10px currentColor';
    });
  });

  // Toggle button logic
  const toggleBtn = panel.querySelector('#toggle-panel-btn');
  let isHidden = false;
  toggleBtn.addEventListener('click', () => {
    isHidden = !isHidden;
    panel.style.display = isHidden ? 'none' : 'block';
  });

  // Keyboard shortcut 'H' to toggle HUD
  window.addEventListener('keydown', (e) => {
    if (e.key === 'h' || e.key === 'H') {
      isHidden = !isHidden;
      panel.style.display = isHidden ? 'none' : 'block';
    }
  });

  // Display the initial trained-model output without changing the initial scene.
  if (engineInstance.engine?.aiModel) {
    renderModelOutput(engineInstance.engine.aiModel.predict(0.60, -0.50));
  }
}
