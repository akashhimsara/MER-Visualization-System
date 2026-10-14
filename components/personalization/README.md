# Adaptive Personalization & User Analytics (Member 4)

## Overview
This component is responsible for analyzing user preferences and selecting optimal visual presets based on real-time emotional analysis of music, adapting continuously to implicit and explicit user feedback.

---

## Milestone 1: Cold-Start Personalization Core
This milestone proves the input/output boundary between **Music Emotion Recognition (MER)** and **Personalization** before integrating reinforcement learning.

### Input
- **MER Tier 3 Event** (`mer.tier3`): Continuous `valence` and `arousal` values within $[-1.0, 1.0]$, `session_id`, `audio_time_ms`, and `sequence`.

### Current Algorithm
- **Deterministic Cold-Start Quadrant Mapping**:
  - Valence $\ge 0$ and Arousal $\ge 0 \rightarrow$ `mock-energetic-positive`
  - Valence $\ge 0$ and Arousal $< 0 \rightarrow$ `mock-calm-positive`
  - Valence $< 0$ and Arousal $\ge 0 \rightarrow$ `mock-tense-negative`
  - Valence $< 0$ and Arousal $< 0 \rightarrow$ `mock-calm-negative`

> **Note on Preset IDs:**
> The mock preset IDs (`mock-energetic-positive`, etc.) are temporary placeholders defined centrally in `components/personalization/presets.py`. They will be replaced by the official visual preset registry managed by the Emotion-Aware Visualization component (Member 2).

### Output
- **Personalization Recommendation Event** (`personalization.recommendation`): Conforms strictly to Contract v1.1 (`contracts/schemas/recommendation.schema.json`).
  - `strategy`: `"cold_start"`
  - `score`: `null` (not fabricated during mock/cold-start)
  - `sequence`: Independent recommendation sequence counter
  - `session_id` and `audio_time_ms`: Preserved from the incoming MER Tier 3 event

---

## Milestone 2: FeedbackEvent -> Reward Processing Layer
This layer converts incoming user feedback into structured scalar reward signals for the contextual bandit (LinUCB) learning loop.

### Processing Pipeline
```text
FeedbackEvent (Contract v1.1)
           ↓
   Reward Processor (calculate_reward)
           ↓
   RewardResult (reward, feedback_type, is_explicit, is_auxiliary)
           ↓
   LinUCB Model Update
```

### Deterministic Reward Policy
The reward policy maps feedback event types to standardized scalar rewards within $[-1.0, +1.0]$:

| Feedback Type | Mapping / Formula | Reward | Signal Category |
| :--- | :--- | :--- | :--- |
| `like` | Direct positive evaluation | `+1.0` | Explicit |
| `dislike` | Direct negative evaluation | `-1.0` | Explicit |
| `rating` | Normalized: `(rating - 3) / 2` | `[-1.0, +1.0]` | Explicit |
| `rating 1` | `(1 - 3) / 2` | `-1.0` | Explicit |
| `rating 2` | `(2 - 3) / 2` | `-0.5` | Explicit |
| `rating 3` | `(3 - 3) / 2` | `0.0` | Explicit |
| `rating 4` | `(4 - 3) / 2` | `+0.5` | Explicit |
| `rating 5` | `(5 - 3) / 2` | `+1.0` | Explicit |
| `preset_select` | User intentionally selects a preset | `+0.75` | Implicit / Behavioral |
| `preset_skip` | User skips past a preset | `-0.75` | Implicit / Behavioral |
| `view_duration` | Dwell time (`duration_ms`) | `None` | Auxiliary / Implicit |

### Policy Notes
1. **Hyperparameters, Not Ground Truth:**
   The numeric reward values (`+1.0`, `-1.0`, `+0.75`, `-0.75`, etc.) are initial policy hyperparameters, **not** objective emotional scores. They are centralized in `components/personalization/feedback.py` and can be tuned or calibrated experimentally.
2. **Deferred View Duration Reward:**
   Raw `duration_ms` is intentionally deferred from producing a direct scalar reward (`reward = None`). Meaningful duration rewards require session-relative context (e.g., track length, average dwell time, relative thresholding) to avoid rewarding inactive or idle tabs. `view_duration` is marked as `is_auxiliary = True` so downstream models can store duration context without corrupting immediate bandit updates.

---

## Milestone 3: Numerical Context Vector Builder
This module constructs a standard numerical context vector from continuous emotion features to serve as the context representation for LinUCB arm selection.

### Processing Pipeline
```text
MER Tier 3 Event (Contract v1.1)
           ↓
   Context Vector Builder (build_context_vector)
           ↓
   ContextVector: [valence, arousal, bias] (dimension = 3)
           ↓
   LinUCB Arm Scoring & Recommendation
```

### Context Vector Specification
The initial context vector $\mathbf{x}_{t}$ has exact dimension $d = 3$:

| Index | Feature Name | Source | Range / Value |
| :---: | :--- | :--- | :--- |
| `0` | `valence` | `tier3_event["emotion"]["valence"]` | $[-1.0, +1.0]$ |
| `1` | `arousal` | `tier3_event["emotion"]["arousal"]` | $[-1.0, +1.0]$ |
| `2` | `bias` | Constant intercept term | `1.0` |

### API & Shadowing Safeguard
- **Dictionary Key:** `"values"` holds the raw list `[valence, arousal, bias]` for JSON/contract compatibility.
- **Typed Attributes:** `.vector` and `.vector_values` provide typed access to the numerical list without shadowing Python's built-in `dict.values()` method.

---

## Milestone 4: Disjoint LinUCB Core
This module implements the standard disjoint LinUCB contextual bandit algorithm (Li et al., 2010) for adaptive visual preset recommendation.

### Processing Pipeline
```text
Numerical Context Vector x_t
           ↓
         LinUCB
           ↓
   Score Candidate Preset Arms
           ↓
      Select Best Preset
```

### Mathematical Formulation
For each candidate arm $a \in \mathcal{A}$:
- **Model State:**
  - $A_a \in \mathbb{R}^{d \times d}$, initialized to identity matrix $I_d$.
  - $b_a \in \mathbb{R}^d$, initialized to zero vector $\mathbf{0}_d$.
- **Ridge Regression Coefficient:**
  $$\hat{\theta}_a = A_a^{-1} b_a$$
  Computed via linear system solving (`np.linalg.solve(A_a, b_a)`).
- **Upper Confidence Bound Scoring:**
  $$\text{exploitation} = \hat{\theta}_a^\top \mathbf{x}_t$$
  $$\text{exploration} = \alpha \sqrt{\mathbf{x}_t^\top A_a^{-1} \mathbf{x}_t}$$
  $$\text{score}_a = \text{exploitation} + \text{exploration}$$
- **Action Selection:**
  $$a_t = \arg\max_{a \in \mathcal{A}} \text{score}_a$$
- **Deterministic Tie-Breaking:**
  At initialization (or when arm scores are strictly equal), the first arm among equal maximum scores in the supplied arm order is chosen without randomness.
- **Model Update:**
  Upon receiving scalar reward $r_t$ for arm $a_t$:
  $$A_{a_t} \leftarrow A_{a_t} + \mathbf{x}_t \mathbf{x}_t^\top$$
  $$b_{a_t} \leftarrow b_{a_t} + r_t \mathbf{x}_t$$

### Configuration & Extensibility
- **Arms:** Injected from the preset registry (`components/personalization/presets.py`).
- **Exploration Parameter:** $\alpha$ defaults to `1.0` and is fully configurable.
- **Status:** The `update(...)` operation is part of the standalone mathematical core; automatic feedback integration into the live pipeline will be connected in a subsequent milestone.
