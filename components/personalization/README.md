# Adaptive Personalization & User Analytics (Member 4)

## Overview
This component is responsible for analyzing user preferences and selecting optimal visual presets based on real-time emotional analysis of music.

## Milestone: Cold-Start Personalization Core
This initial milestone proves the input/output boundary between **Music Emotion Recognition (MER)** and **Personalization** before integrating reinforcement learning.

### Input
- **MER Tier 3 Event** (`mer.tier3`): Continuous `valence` and `arousal` values within $[-1.0, 1.0]$, `session_id`, `audio_time_ms`, and `sequence`.

### Current Algorithm
- **Deterministic Cold-Start Quadrant Mapping**:
  - Valence $\ge 0$ and Arousal $\ge 0 ightarrow$ `mock-energetic-positive`
  - Valence $\ge 0$ and Arousal $< 0 ightarrow$ `mock-calm-positive`
  - Valence $< 0$ and Arousal $\ge 0 ightarrow$ `mock-tense-negative`
  - Valence $< 0$ and Arousal $< 0 ightarrow$ `mock-calm-negative`

> **Note on Preset IDs:**
> The mock preset IDs (`mock-energetic-positive`, etc.) are temporary placeholders defined centrally in `components/personalization/presets.py`. They will be replaced by the official visual preset registry managed by the Emotion-Aware Visualization component (Member 2).

### Output
- **Personalization Recommendation Event** (`personalization.recommendation`): Conforms strictly to Contract v1.1 (`contracts/schemas/recommendation.schema.json`).
  - `strategy`: `"cold_start"`
  - `score`: `null` (not fabricated during mock/cold-start)
  - `sequence`: Independent recommendation sequence counter
  - `session_id` and `audio_time_ms`: Preserved from the incoming MER Tier 3 event

### Future Extension
- The quadrant mapping policy will be replaced by a **LinUCB** contextual bandit algorithm learning from user feedback events (`feedback.event`) while maintaining identical Contract v1.1 recommendation output boundaries.
