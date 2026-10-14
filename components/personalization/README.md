# Adaptive Personalization & User Analytics (Member 4)

## Overview
This component is responsible for analyzing user preferences and selecting optimal visual presets based on real-time emotional analysis of music, adapting continuously to implicit and explicit user feedback.

## Milestone 1: Cold-Start Personalization Core
This milestone proves the input/output boundary between **Music Emotion Recognition (MER)** and **Personalization** before integrating reinforcement learning.

### Input
- **MER Tier 3 Event** (`mer.tier3`): Continuous `valence` and `arousal` values within $[-1.0, 1.0]$, `session_id`, `audio_time_ms`, and `sequence`.

### Current Algorithm
- **Deterministic Cold-Start Quadrant Mapping**:
  - Valence $\ge 0$ and Arousal $\ge 0
ightarrow$ `mock-energetic-positive`
  - Valence $\ge 0$ and Arousal $< 0
ightarrow$ `mock-calm-positive`
  - Valence $< 0$ and Arousal $\ge 0
ightarrow$ `mock-tense-negative`
  - Valence $< 0$ and Arousal $< 0
ightarrow$ `mock-calm-negative`

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

This layer converts incoming user feedback into structured scalar reward signals for the upcoming contextual bandit (LinUCB) learning loop.

### Processing Pipeline
```text
FeedbackEvent (Contract v1.1)
           ↓
   Reward Processor (calculate_reward)
           ↓
   RewardResult (reward, feedback_type, is_explicit, is_auxiliary)
           ↓
   Future: LinUCB Policy Model Update
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

### Important Policy Notes
1. **Hyperparameters, Not Ground Truth:**
   The numeric reward values (`+1.0`, `-1.0`, `+0.75`, `-0.75`, etc.) are initial policy hyperparameters, **not** objective emotional scores. They are centralized in `components/personalization/feedback.py` and can be tuned or calibrated experimentally.
2. **Deferred View Duration Reward:**
   Raw `duration_ms` is intentionally deferred from producing a direct scalar reward (`reward = None`). Meaningful duration rewards require session-relative context (e.g., track length, average dwell time, relative thresholding) to avoid rewarding inactive or idle tabs. `view_duration` is marked as `is_auxiliary = True` so downstream models can store duration context without corrupting immediate bandit updates.

---

## Future Roadmap: LinUCB Policy
Once the input/output boundaries and reward processing layer are verified:
1. Replace `cold_start` with an active LinUCB contextual bandit.
2. Context vector $\mathbf{x}_{t}$ derived from current MER Tier 1-3 features.
3. Arm set $\mathcal{A}$ mapped to visual presets.
4. Model update: update covariance matrix $A_{a}$ and response vector $b_{a}$ using computed $r_{t}$ from `calculate_reward(feedback_event)`.
