# PROJECT HANDOFF & MASTER RESEARCH PLAN
## Emotion Adaptive Real-Time Music Visualization System

---

### 1. Purpose & Scope
This document defines the authoritative research basis, team boundaries, component scope, dataset strategy, AI pipeline, 50% milestone definition, and implementation roadmap for the undergraduate research project **"Emotion Adaptive Real-Time Music Visualization System"**.

---

### 2. User Component & Team Boundaries

#### **User Role**: Member 2
#### **Individual Component**: AI-Assisted Emotion-Aware Visualization Engine
#### **Core Pitch**:
> "My component takes a detected music emotion (Valence / Arousal) and uses an AI model to predict a visual parameter vector. Three.js then consumes those parameters to create a real-time emotion-aware visualization."

```
[Music Audio] ──> [Member 1: MER] ──> [Valence / Arousal] ──> [User / Member 2: AI Mapping Model] ──> [Predicted Visual Parameters] ──> [Three.js Engine]
```

#### **Team Boundaries Matrix**:
| Member | Component | Owns | Does NOT Own |
|---|---|---|---|
| **Member 1** | Music Emotion Recognition (MER) | Extract/detect emotion (Valence/Arousal) from music audio | Visual parameter generation |
| **Member 2 (User)** | **AI-Assisted Emotion-Aware Visualization Engine** | **Emotion $\rightarrow$ AI Visual Parameters $\rightarrow$ Three.js Rendering** | **MER, transition timing, personalization** |
| **Member 3** | Emotion-Based Visual Transition System | Emotion-change detection/smoothing & transition timing | Core emotion-to-visual parameter generation |
| **Member 4** | Preference / Recommendation / Analytics | Preference learning & recommendation analytics | User's core visualization mapping |

---

### 3. Visual Engine Scope (Three.js Layer)
Visual parameters predicted by AI and rendered in Three.js:
- **Colour**: Base hue, saturation, brightness, gradient palettes.
- **Particle System**: Particle density, size, speed, spread, floating drift.
- **Animation / Motion**: Motion speed, turbulence intensity, wave amplitude, beat-reactive bounce.
- **Lighting & Glow**: Studio key light, ambient light intensity, point light color, post-processing bloom strength.
- **Target Quality**: Dynamic, attractive, high-quality EDM-style visuals.

---

### 4. Verified Dataset Facts & Strategy

1. **DEAM (Database for Emotional Analysis in Music)**:
   - Official source: `https://cvml.unige.ch/databases/DEAM/`
   - Contains: 1,802 music excerpts with continuous valence and arousal annotations.
   - Purpose: Music emotion input benchmark (Member 1 MER / Emotion Coordinates).
2. **EmoSet**:
   - Official ICCV 2023 Paper: `https://openaccess.thecvf.com/content/ICCV2023/html/Yang_EmoSet_A_Large-scale_Visual_Emotion_Dataset_with_Rich_Attributes_ICCV_2023_paper.html`
   - Contains: 3.3 million images (118,102 human-labelled) across 8 visual emotion categories.
   - Purpose: Visual emotion attribute evidence (brightness, colorfulness, scene type).
3. **Research-Based Controlled Mapping Records**:
   - Final dataset prepared for User's AI Mapping Experiment based on published literature:
     - **Fonteles et al. (2013)**: 3D particle-system music visualization.
     - **Dharmapriya et al. (2021)**: Music emotion-to-colour mapping.
     - **Kurilcik et al. (2024)**: Sound, color, and emotion relationships.
     - **Hsiao et al. (2017)**: Stage lighting control based on music emotions (2,087 song clips).
     - **Huang et al. (2025)**: Deep learning music visualization.

---

### 5. Proposed Mapping Dataset Schema

| Column Name | Data Type | Description / Range |
|---|---|---|
| `emotion` | String | CALM, HAPPY, ENERGETIC, SAD |
| `valence` | Float | Positivity score (-1.0 to +1.0) |
| `arousal` | Float | Energy score (-1.0 to +1.0) |
| `hue` | Float | Color hue angle (0.0 to 1.0) |
| `saturation` | Float | Color saturation (0.0 to 1.0) |
| `brightness` | Float | Color lightness/brightness (0.0 to 1.0) |
| `particle_density` | Integer | Particle count (100 to 1000) |
| `particle_size` | Float | Point size (0.1 to 1.0) |
| `particle_speed` | Float | Drift velocity multiplier (0.1 to 3.0) |
| `animation_speed` | Float | Animation frequency multiplier (0.1 to 3.0) |
| `motion_intensity` | Float | Bouncing/wave turbulence scalar (0.1 to 3.0) |
| `lighting_intensity` | Float | Point light brightness scalar (0.2 to 5.0) |
| `lighting_colour` | Hex String | Studio light color hex |

---

### 6. AI Model Architecture Pipeline
```
[Valence, Arousal] ──> [AI Mapping Model (Regression / Neural Net)] ──> [Predicted Visual Parameter Vector] ──> [JSON / JS API] ──> [Engine.updateVisualParameters()]
```

---

### 7. Non-Negotiable Research Rules
1. **Never invent dataset sample counts.**
2. **Never claim a dataset contains labels that it does not contain.**
3. **Never invent questionnaire/interview results.**
4. **Never report made-up model accuracy.**
5. **Separate existing dataset facts from researcher-created mapping records.**
6. **Keep Member 1, Member 2, and Member 3 boundaries strictly separate.**
7. **Execute step-by-step with clear verification before proceeding to the next feature.**
