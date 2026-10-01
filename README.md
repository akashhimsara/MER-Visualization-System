# AI-Assisted Emotion-Aware Visualization Engine

> **Research Project Component:** Emotion Adaptive Real-Time Music Visualization System  
> **Individual Component:** AI-Assisted Emotion-Aware Visualization Engine  
> **Core Pipeline:** $\text{Emotion} \longrightarrow \text{Visual Parameters} \longrightarrow \text{Three.js} \longrightarrow \text{Real-Time Visualization}$

---

## 📌 Architecture & Module Overview

```
MER-Visualization-System/
├── index.html                     # Web Viewport Container
├── package.json                   # Dependencies & Build Scripts
├── src/
│   ├── index.js                   # 🌟 Public Facade API (VisualizationEngine)
│   ├── main.js                    # Application Bootstrapper
│   ├── style.css                  # Viewport Styling
│   ├── visual-engine/
│   │   ├── Engine.js              # Three.js Lifecycle & Render Loop Orchestrator
│   │   ├── scene.js               # 3D Scene Initialization & Geometry Setup
│   │   ├── camera.js              # Perspective Camera & Viewport Calculations
│   │   └── renderer.js            # WebGL Renderer & DPI Optimization
│   ├── visuals/
│   │   ├── particles.js           # 1,000 GPU BufferGeometry Particle Engine
│   │   ├── color.js               # Color Manipulation & Smooth Lerp Module
│   │   ├── animation.js           # Motion Speed, Wave Turbulence & Rotation Engine
│   │   ├── lighting.js            # AmbientLight & Specular PointLight Controller
│   │   ├── parameters.js          # Unified Visual Parameter Controller Interface
│   │   ├── emotions.js            # Emotion Presets Mappings (CALM, HAPPY, ENERGETIC, SAD)
│   │   └── transitions.js         # Smooth Ease-In-Out Cubic Emotion Transition Manager
│   └── ui/
│       └── debug-panel.js         # Interactive Glassmorphic Control Overlay & HUD
```

---

## 🚀 Quick Start Guide

### 1. Installation & Running Locally

```bash
# Install dependencies
npm install

# Run Vite dev server
npm run dev

# Build production bundle
npm run build
```

---

## 🔌 Team Integration & API Reference

### Initializing the Engine

```javascript
import { VisualizationEngine } from './src/index.js';

// Instantiate engine on target DOM container
const vizEngine = new VisualizationEngine(document.getElementById('app'));

// Start 60 FPS WebGL render loop
vizEngine.start();
```

### Triggering Emotion Transitions

Pass an emotion key (`'CALM'`, `'HAPPY'`, `'ENERGETIC'`, `'SAD'`) along with an optional transition duration in seconds:

```javascript
// 2-second smooth transition to HAPPY
vizEngine.setEmotion('HAPPY', 2.0);

// 1.5-second transition to ENERGETIC
vizEngine.setEmotion('ENERGETIC', 1.5);

// 3-second transition to CALM
vizEngine.setEmotion('CALM', 3.0);
```

### Passing Custom Visual Parameters

For direct AI model parameter output:

```javascript
vizEngine.updateParameters({
  particleColor: 0xff0055,   // Hex or string color
  motionSpeed: 2.2,         // Speed scalar (0.1 - 3.0)
  motionIntensity: 2.0,     // Wave amplitude scalar (0.0 - 3.0)
  lightColor: 0xff00aa,      // Specular light color
  lightIntensity: 2.5       // Light brightness scalar
});
```

---

## 🎛️ Interactive Debug HUD

- Built-in developer HUD attached at top-right of browser viewport.
- Press **`H`** key on keyboard to toggle HUD visibility during presentations.

---

## 🛡️ Scope Boundaries

- 🟢 **Music Emotion Recognition (MER)**: Excluded (handled by designated teammate).
- 🟢 **Emotion Transition System**: Excluded (handled by designated teammate).
- 🟢 **Personalization / Datasets**: Excluded.
- 🟢 **Version Control**: Git push executed strictly on explicit user command.
