/**
 * Creates the focused standalone Member 2 viva interface.
 * The manual emotion samples simulate the future Member 1 VA input.
 */
export function createDebugPanel(engineInstance) {
  if (!engineInstance) return;

  const audioElement = document.createElement('audio');
  audioElement.id = 'viz-audio-player';
  audioElement.controls = false;
  document.body.appendChild(audioElement);
  engineInstance.engine?.connectAudioElement?.(audioElement);

  const panel = document.createElement('aside');
  panel.id = 'viva-panel';
  Object.assign(panel.style, {
    position: 'fixed', top: '20px', right: '20px', zIndex: '9999', width: '300px',
    padding: '18px', borderRadius: '18px', color: '#edfaff', fontFamily: 'Inter, system-ui, sans-serif',
    background: 'linear-gradient(160deg, rgba(10,16,31,.92), rgba(12,10,27,.88))',
    border: '1px solid rgba(116, 236, 255, .24)', boxShadow: '0 18px 50px rgba(0,0,0,.45)',
    backdropFilter: 'blur(18px)'
  });

  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:16px;">
      <div>
        <div style="font-size:10px;letter-spacing:1.3px;color:#72eaff;font-weight:800;">MEMBER 2 · 50% VIVA</div>
        <div style="font-size:18px;font-weight:800;letter-spacing:-.4px;margin-top:3px;">Emotion Visual Lab</div>
      </div>
      <span style="font-size:10px;color:#80ffc7;border:1px solid rgba(128,255,199,.3);padding:4px 7px;border-radius:99px;">LIVE</span>
    </div>

    <section style="margin-bottom:14px;">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:7px;"><span style="display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#20d6ed;color:#051015;font-size:11px;font-weight:900;">1</span><b style="font-size:12px;">Upload a song</b></div>
      <input id="audio-file-input" type="file" accept="audio/*" style="display:none" />
      <button id="choose-audio-btn" style="width:100%;padding:11px;border-radius:10px;border:1px solid #21d8ed;background:rgba(24,201,223,.13);color:#8cf9ff;font-weight:800;cursor:pointer;">Upload MP3 / Music File</button>
      <div id="audio-filename" style="font-size:10px;color:#8493aa;margin:7px 2px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">No song selected yet</div>
    </section>

    <section id="emotion-step" style="margin-bottom:14px;opacity:.42;pointer-events:none;transition:opacity .25s;">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:7px;"><span style="display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#6e5dff;color:white;font-size:11px;font-weight:900;">2</span><b style="font-size:12px;">Choose a sample emotion</b></div>
      <div style="font-size:10px;line-height:1.35;color:#91a1b9;margin:0 0 8px;">Temporary input until Member 1 emotion output is connected.</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;">
        <button class="emotion-btn" data-emotion="CALM" style="padding:9px;border-radius:9px;border:1px solid #32d7ff;background:rgba(50,215,255,.08);color:#75e8ff;font-weight:800;cursor:pointer;">CALM</button>
        <button class="emotion-btn" data-emotion="HAPPY" style="padding:9px;border-radius:9px;border:1px solid #ffd55d;background:rgba(255,213,93,.08);color:#ffe188;font-weight:800;cursor:pointer;">HAPPY</button>
        <button class="emotion-btn" data-emotion="ENERGETIC" style="padding:9px;border-radius:9px;border:1px solid #ff5ba6;background:rgba(255,91,166,.08);color:#ff87be;font-weight:800;cursor:pointer;">ENERGETIC</button>
        <button class="emotion-btn" data-emotion="SAD" style="padding:9px;border-radius:9px;border:1px solid #8da5ff;background:rgba(141,165,255,.08);color:#a9baff;font-weight:800;cursor:pointer;">SAD</button>
      </div>
      <button id="random-emotion-btn" style="width:100%;margin-top:7px;padding:8px;border-radius:9px;border:1px dashed rgba(213,180,255,.55);background:rgba(150,96,255,.10);color:#decaff;font-weight:750;cursor:pointer;">✦ Select Random Sample</button>
    </section>

    <section id="ready-card" style="display:none;margin-bottom:14px;padding:11px;border-radius:12px;background:linear-gradient(135deg,rgba(43,218,255,.13),rgba(185,93,255,.12));border:1px solid rgba(110,233,255,.32);">
        <div style="font-size:10px;letter-spacing:.8px;color:#97eaff;font-weight:800;">VISUAL DNA GENERATED · ROSE PREVIEW</div>
      <div id="recipe-summary" style="font-size:11px;line-height:1.5;color:#e5f9ff;margin-top:5px;">Waiting for input</div>
    </section>

    <section id="play-step" style="opacity:.42;pointer-events:none;transition:opacity .25s;">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:7px;"><span style="display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#2de69b;color:#03150c;font-size:11px;font-weight:900;">3</span><b style="font-size:12px;">Play the live visualization</b></div>
      <div style="display:flex;gap:8px;">
        <button id="play-audio-btn" style="flex:1;padding:10px;border-radius:9px;border:1px solid #2de69b;background:rgba(45,230,155,.12);color:#69ffc1;font-weight:850;cursor:pointer;">▶ Play</button>
        <button id="pause-audio-btn" style="flex:1;padding:10px;border-radius:9px;border:1px solid #ffd05d;background:rgba(255,208,93,.10);color:#ffd879;font-weight:850;cursor:pointer;">Ⅱ Pause</button>
      </div>
    </section>

    <div id="live-reaction" style="display:none;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.10);">
      <div style="display:flex;justify-content:space-between;font-size:10px;margin-bottom:5px;"><b style="color:#65ffc0;">LIVE AUDIO REACTION</b><span id="beat-status" style="color:#7e8da7;">LISTENING</span></div>
      <div id="audio-values" style="font-size:10px;color:#c2cde2;">Bass -- | Mid -- | High --</div>
    </div>

    <details style="margin-top:14px;border-top:1px solid rgba(255,255,255,.10);padding-top:10px;">
      <summary style="cursor:pointer;color:#94a1bc;font-size:10px;font-weight:700;">Viva evidence details</summary>
      <div id="model-evidence" style="margin-top:7px;font-size:10px;line-height:1.5;color:#c8d5e8;">Dataset → trained model → visual parameters</div>
    </details>
  `;
  document.body.appendChild(panel);

  const fileInput = panel.querySelector('#audio-file-input');
  const chooseButton = panel.querySelector('#choose-audio-btn');
  const filename = panel.querySelector('#audio-filename');
  const emotionStep = panel.querySelector('#emotion-step');
  const playStep = panel.querySelector('#play-step');
  const readyCard = panel.querySelector('#ready-card');
  const recipeSummary = panel.querySelector('#recipe-summary');
  const modelEvidence = panel.querySelector('#model-evidence');
  const liveReaction = panel.querySelector('#live-reaction');
  const audioValues = panel.querySelector('#audio-values');
  const beatStatus = panel.querySelector('#beat-status');
  const emotionButtons = [...panel.querySelectorAll('.emotion-btn')];
  const randomButton = panel.querySelector('#random-emotion-btn');

  const setSelectedEmotion = (emotion) => {
    const prediction = engineInstance.setEmotion(emotion, 1.2);
    emotionButtons.forEach((button) => {
      const selected = button.dataset.emotion === emotion;
      button.style.opacity = selected ? '1' : '.45';
      button.style.boxShadow = selected ? '0 0 16px currentColor' : 'none';
    });
    modelEvidence.textContent = `Sample input: ${emotion}. Model output: ${prediction.particleDensity} particles, speed ${prediction.motionSpeed.toFixed(2)}, bloom ${prediction.bloomStrength.toFixed(2)}.`;
  };

  chooseButton.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    filename.textContent = file.name;
    engineInstance.engine?.loadAudioFile?.(file);
    emotionStep.style.opacity = '1';
    emotionStep.style.pointerEvents = 'auto';
    readyCard.style.display = 'none';
    playStep.style.opacity = '.42';
    playStep.style.pointerEvents = 'none';
    liveReaction.style.display = 'none';
    emotionButtons.forEach((button) => { button.style.opacity = '1'; button.style.boxShadow = 'none'; });
    modelEvidence.textContent = 'Song loaded. Select one sample emotion to generate its visual recipe.';
  });

  emotionButtons.forEach((button) => button.addEventListener('click', () => setSelectedEmotion(button.dataset.emotion)));
  randomButton.addEventListener('click', () => {
    const emotions = ['CALM', 'HAPPY', 'ENERGETIC', 'SAD'];
    setSelectedEmotion(emotions[Math.floor(Math.random() * emotions.length)]);
  });

  window.addEventListener('songvisualdna', (event) => {
    const recipe = event.detail;
    if (!recipe) return;
    const palette = `#${recipe.palette.primary.toString(16).padStart(6, '0').toUpperCase()}`;
    readyCard.style.display = 'block';
    recipeSummary.textContent = `${recipe.emotionCategory} · ${recipe.visualMode.replaceAll('_', ' ')} · Seed ${recipe.seed.toString(16).toUpperCase()} · ${palette}`;
    playStep.style.opacity = '1';
    playStep.style.pointerEvents = 'auto';
  });

  panel.querySelector('#play-audio-btn').addEventListener('click', async () => {
    await engineInstance.engine?.playAudio?.();
    liveReaction.style.display = 'block';
  });
  panel.querySelector('#pause-audio-btn').addEventListener('click', () => engineInstance.engine?.pauseAudio?.());

  window.addEventListener('audioanalysis', (event) => {
    const metrics = event.detail;
    if (!metrics) return;
    audioValues.textContent = `Bass ${metrics.bass.toFixed(2)} | Mid ${metrics.mid.toFixed(2)} | High ${metrics.high.toFixed(2)}`;
    beatStatus.textContent = metrics.isBeat ? 'BEAT!' : metrics.profile;
    beatStatus.style.color = metrics.isBeat ? '#ffd05d' : '#65ffc0';
  });
}
