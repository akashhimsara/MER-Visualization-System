# Adaptive Personalization & User Analytics (Member 4)

## Architecture Overview

The Adaptive Personalization component dynamically recommends visual presets based on real-time emotion recognition (MER Tier 3 continuous valence and arousal) and learns individual user preferences over time via contextual bandit algorithms (LinUCB).

The component operates in two distinct phases:
1. **Cold-Start Policy:** Deterministic quadrant-based mapping active during initial user sessions when no feedback has been recorded.
2. **Adaptive Personalization (LinUCB):** Contextual multi-armed bandit algorithm that balances exploitation (recommending presets with high predicted reward) and exploration (sampling presets with high uncertainty) once reward feedback is observed.

---

## Milestone 1: Cold-Start Personalization Core

### Cold-Start Quadrant Mapping

Continuous valence and arousal are partitioned across the origin:

| Quadrant | Valence | Arousal | Target Mood | Temporary Mock Preset ID |
| :--- | :--- | :--- | :--- | :--- |
| **Q1** | $\ge 0.0$ | $\ge 0.0$ | Energetic Positive | `mock-energetic-positive` |
| **Q2** | $\ge 0.0$ | $< 0.0$ | Calm Positive | `mock-calm-positive` |
| **Q3** | $< 0.0$ | $\ge 0.0$ | Tense Negative | `mock-tense-negative` |
| **Q4** | $< 0.0$ | $< 0.0$ | Calm Negative | `mock-calm-negative` |

---

## Milestone 2: Feedback & Reward Processing Layer

### Reward Policy

Converts Contract v1.1 `feedback.event` payloads into scalar learning rewards:

| Feedback Type | Category | Value / Normalization | Reward Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `like` | Explicit | Fixed $+1.0$ | $+1.0$ | Direct positive preference. |
| `dislike` | Explicit | Fixed $-1.0$ | $-1.0$ | Direct negative preference. |
| `rating` | Explicit | $(rating - 3) / 2$ | $[-1.0, +1.0]$ | 1 $\rightarrow -1.0$, 3 $\rightarrow 0.0$, 5 $\rightarrow +1.0$. |
| `preset_select` | Implicit | Fixed $+0.75$ | $+0.75$ | User manually selects recommended preset. |
| `preset_skip` | Implicit | Fixed $-0.75$ | $-0.75$ | User explicitly skips recommended preset. |
| `view_duration` | Auxiliary | `None` (deferred) | `None` | Auxiliary engagement telemetry; does not directly update LinUCB. |

---

## Milestone 3: Numerical Context Vector Builder

Extracts continuous valence and arousal from MER Tier 3 events and constructs a standardized fixed-dimension feature vector:

$$\mathbf{x} = [\text{valence}, \text{arousal}, \text{bias}]^\top \in \mathbb{R}^3$$

---

## Milestone 4: Disjoint LinUCB Core

For each candidate preset arm $a \in \mathcal{A}$:
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
- **Deterministic Tie-Breaking:**
  First arm among equal maximum scores wins strictly (`score > best_score`).
- **Model Update:**
  $$A_{a_t} \leftarrow A_{a_t} + \mathbf{x}_t \mathbf{x}_t^\top$$
  $$b_{a_t} \leftarrow b_{a_t} + r_t \mathbf{x}_t$$

---

## Milestone 5: Closed In-Memory Learning Loop

The `AdaptivePersonalizationEngine` connects all personalization sub-components into an end-to-end adaptive loop:

### Pipeline Flow
```text
MER Tier 3 Event
       ↓
Context Vector Builder: [valence, arousal, bias]
       ↓
Cold-Start / LinUCB Selection
       ↓
Contract v1.1 Recommendation Event
       ↓
User Interaction & FeedbackEvent
       ↓
Reward Processor: calculate_reward(...)
       ↓
LinUCB Model Update: LinUCB.update(...)
       ↓
Future Recommendations Adapt
```

### Transition Rule
- **`successful_update_count == 0`**:
  Uses deterministic quadrant cold-start policy (`strategy="cold_start"`, `score=null`).
- **`successful_update_count >= 1`**:
  Uses LinUCB arm selection (`strategy="linucb"`, `score=float`).

### In-Memory Interaction Matching Policy
Because Contract v1.1 `feedback.event` contains `preset_id` and `session_id` but does not include `recommendation_id`, feedback events match the **most recent unprocessed pending interaction** with the same `(session_id, preset_id)`.
> **Milestone Limitation:** This matching policy is an in-memory design for the current milestone. It will be replaced with persistent interaction IDs or contract evolution when PostgreSQL persistence is added.

### Duplicate Feedback Protection
Processed `feedback_id` values are retained in memory. If the same `feedback_id` is submitted multiple times, it is safely ignored (`status="duplicate"`, `applied=False`), preventing duplicate updates from corrupting bandit state.

### Auxiliary Feedback Handling
Events such as `view_duration` return `reward = None`. They are recorded as auxiliary telemetry (`status="auxiliary"`, `applied=False`) and do **not** trigger LinUCB updates or transition the engine out of cold-start.
