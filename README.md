# Emotion-Adaptive Real-Time Music Visualization System

**Project ID:** J26-IT-456

A research-oriented real-time music visualization system that analyses musical emotion and acoustic characteristics, converts them into meaningful visual states, controls smooth emotion-aware visual transitions, and adapts visualization recommendations according to individual user preferences.

The project is developed as a four-member final-year research project using a modular monorepo architecture so that each research component can be developed, evaluated, and integrated independently.

---

## Research Components

The system consists of four main research components.

### 1. Music Emotion Recognition

Responsible for real-time music analysis and continuous emotion estimation.

Main responsibilities include:

- Continuous Valence-Arousal prediction
- Lightweight acoustic feature extraction
- Onset and rhythmic analysis
- Tempo estimation
- Multi-tier real-time processing
- MER performance and latency evaluation

Primary emotion representation:

```text
Valence: -1.0 to +1.0
Arousal: -1.0 to +1.0
```

The initial pretrained music representation candidate is **MERT-v1-95M**.

---

### 2. Emotion-Aware Visualization

Responsible for converting emotion and audio information into real-time visual states.

Main responsibilities include:

- Emotion-to-visual mapping
- Visual preset definition
- Particle behaviour
- Colour mapping
- Lighting
- Motion and animation
- Three.js rendering
- Visualization performance evaluation

The visualization engine is implemented using **Three.js**.

---

### 3. Emotion-Based Visual Transition

Responsible for deciding when and how visual states should transition.

Main responsibilities include:

- Temporal emotion analysis
- Emotion smoothing
- Meaningful emotion-change detection
- Transition candidate generation
- Transition suitability scoring
- Cooldown and continuity control
- Transition timing, duration, and strength

This component does not generate visual designs. It controls transitions between visual states produced by the visualization component.

---

### 4. Adaptive Personalization & User Analytics

Responsible for learning individual visualization preferences and improving recommendations over time.

Main responsibilities include:

- User preference management
- Explicit and implicit feedback collection
- Interaction-history analysis
- Visualization recommendation
- Cold-start handling
- User analytics
- Preference learning

The initial personalization approach will investigate **LinUCB contextual bandits**.

---

## High-Level System Flow

```text
Audio File / Microphone
          |
          v
Music Emotion Recognition
          |
          |-- Tier 1: Acoustic Features
          |-- Tier 2: Tempo
          |-- Tier 3: Valence-Arousal
          |
          +----------------------+
          |                      |
          v                      v
Personalization          Transition Analysis
          |                      |
          v                      |
Visualization Mapping            |
          |                      |
          v                      |
Target Visual State -------------+
          |
          v
Transition Command
          |
          v
Three.js Renderer
          |
          v
User
          |
          v
Feedback / Interaction History
          |
          v
Personalization
```

---

## Technology Stack

### Frontend

- React
- TypeScript
- Vite

### Visualization

- Three.js

### Backend

- Python
- FastAPI

### Communication

- WebSocket for real-time communication
- REST APIs for standard operations

### Database

- PostgreSQL 18

### Authentication

Planned authentication stack:

- JWT
- PyJWT
- pwdlib
- Argon2 password hashing

### Machine Learning and Audio Processing

Planned libraries include:

- PyTorch
- librosa
- NumPy
- pandas
- scikit-learn

### Music Emotion Recognition

- MERT-v1-95M as the initial pretrained candidate
- Traditional engineered-feature baseline
- Hybrid representation experiments

### Personalization

- LinUCB contextual bandit

### Shared Interfaces

- JSON Schema Draft 2020-12

---

## Repository Structure

```text
MER-Visualization-System/
|
├── apps/
│   ├── web/                     # React + TypeScript + Vite frontend
│   └── api/                     # FastAPI integration backend
│
├── components/
│   ├── mer/                     # Music Emotion Recognition
│   ├── visualization/           # Emotion-aware visualization research
│   ├── transition/              # Emotion-based transition research
│   └── personalization/         # Personalization and analytics
│
├── packages/
│   └── visualization-core/      # Reusable Three.js visualization runtime
│
├── contracts/
│   ├── schemas/                 # Shared JSON schemas
│   ├── examples/                # Example contract messages
│   └── README.md
│
├── mocks/                       # Mock component outputs for parallel development
├── tests/                       # Shared integration and system tests
├── data/                        # Dataset-related workspace
├── model_artifacts/             # Model artifact documentation/storage references
├── docs/                        # Shared project documentation
├── scripts/                     # Utility and setup scripts
├── infra/                       # Infrastructure/deployment configuration
│
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
└── README.md
```

The repository is intentionally kept shallow during the initial scaffold stage. Deeper component-specific structures will be introduced when the existing research implementations are migrated.

---

## Shared Contract Principle

All research components communicate through versioned shared contracts.

The `contracts/` directory is the source of truth for cross-component data structures.

The canonical cross-component emotion representation is:

```text
continuous Valence-Arousal
```

Categorical labels such as:

```text
HAPPY
SAD
CALM
ENERGETIC
EXCITED
TENSE
```

may be derived internally by individual components but must not be used as the primary shared emotion representation.

Breaking contract changes require agreement from affected team members.

---

## Development Setup

### Prerequisites

Install:

- Git
- Node.js with npm
- Python 3.11 or another project-approved Python version

PostgreSQL will be configured during a later development stage.

---

## Running the Frontend

From the repository root:

```bash
cd apps/web
npm install
npm run dev
```

The Vite development server should normally become available at:

```text
http://localhost:5173
```

Create a production build using:

```bash
npm run build
```

---

## Running the Backend

Navigate to:

```bash
cd apps/api
```

### Windows PowerShell

If the virtual environment does not exist:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

The backend should become available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Environment Variables

Copy the configuration template when environment-specific configuration becomes necessary:

```text
.env.example
```

Do not commit real secrets, database passwords, API keys, or JWT secrets.

---

## Git Workflow

The project follows the basic branch structure:

```text
main
  |
develop
  |
feature/*
```

Examples:

```text
feature/contracts-v1.1
feature/mer-runtime
feature/visualization-engine
feature/transition-engine
feature/personalization
```

Do not push experimental development directly to `main`.

Refer to `CONTRIBUTING.md` for team development rules.

---

## Repository Rules

Do not commit:

- `node_modules`
- Python virtual environments
- raw research datasets
- large audio collections
- model checkpoints
- temporary experiment outputs
- `.env` files containing secrets

Large research artifacts should be managed separately from normal Git history.

---

## Current Project Status

The repository is currently in the **initial scaffold and integration-contract stage**.

Currently available:

- React + TypeScript + Vite frontend scaffold
- Three.js frontend dependency
- FastAPI backend scaffold
- `/health` backend endpoint
- Monorepo component structure
- Shared contract workspace
- Research component placeholders

Not yet integrated:

- Existing Member 1 MER implementation
- Existing Member 2 visualization prototype
- Existing Member 3 transition implementation
- Member 4 personalization implementation
- PostgreSQL
- Authentication
- Runtime WebSocket pipeline
- Full Contract v1.1 schemas
- End-to-end audio-to-visual pipeline

Existing research implementations will be migrated incrementally after the shared contracts are finalized.

---

## Development Principle

Each research component should remain internally independent.

A component may change its internal algorithm or implementation without requiring changes to other components as long as it continues to satisfy the agreed shared contracts.

For example:

```text
MER model implementation changes
        |
        v
Shared MER contract remains unchanged
        |
        v
Visualization / Transition / Personalization continue working
```

This allows all four team members to develop and test their research components in parallel.

---

## Project Stage

**Current stage:** Initial architecture scaffold and shared contract definition.
