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

---

## Milestone 6: User History & Preferences Layer

The `UserPersonalizationState` provides structured tracking of user-level history, interaction counts, and learned preference summaries:

### Pipeline Integration
```text
Adaptive Recommendation
       ↓
Feedback
       ↓
Reward
       ↓
User History / Preference Summary
       ↓
LinUCB Learning
```

- **Separation of Concerns:** `UserPersonalizationState` tracks high-level interaction history and preferences. LinUCB covariance matrices ($A_a, b_a$) remain strictly owned by `LinUCB` inside `AdaptivePersonalizationEngine`.
- **Bounded Recent History:** `recent_recommendations` and `recent_feedback` records are bounded (default size `20`) to prevent unbounded memory growth.
- **Deterministic Summaries:** Preference resolution methods (`get_most_positively_rewarded_preset`, etc.) break ties deterministically by preset identifier.

---

## Milestone 7: PostgreSQL Persistence Layer

The persistence layer allows personalization history, user preferences, and LinUCB bandit parameters to survive server restarts.

### Layered Architecture
```text
Personalization Engine (AdaptivePersonalizationEngine / LinUCB)
       ↓
Persistence Repository (PersonalizationRepository)
       ↓
SQLAlchemy ORM (Models & Portable JSON Serializers)
       ↓
PostgreSQL Database
```

### Persisted Database Entities
1. **`personalization_user_state`**:
   Tracks total recommendations, feedback count, successful learning updates, cumulative reward, numerical reward count, last recommended preset, and last feedback type.
2. **`personalization_preset_stats`**:
   Tracks per-preset interaction counters (`like`, `dislike`, `rating`, `select`, `skip`, `view_duration`), rating sum, and cumulative reward. Composite unique constraint on `(user_id, preset_id)`.
3. **`personalization_linucb_state`**:
   Stores LinUCB design covariance matrices ($A_a$) and bias vectors ($b_a$) per arm as portable JSON arrays with strict shape validation (`(d, d)` and `(d,)`). Composite unique constraint on `(user_id, arm_id)`.
4. **`personalization_interactions`**:
   Persists emitted recommendations and context vectors (`[valence, arousal, bias]`), indexed by unique `recommendation_id`.
5. **`personalization_processed_feedback`**:
   Idempotency log tracking processed `feedback_id` values to ensure duplicate submissions cannot corrupt bandit state or reward metrics across restarts.

### Database Configuration & Migrations
- **Configuration:** Connection string read from `DATABASE_URL` environment variable (defaults to `.env.example`).
- **Alembic Migrations:**
  ```bash
  # View current migration heads
  python -m alembic heads

  # Apply all migrations to the database
  python -m alembic upgrade head

  # Rollback migration
  python -m alembic downgrade -1
  ```

### State Restoration Flow
```python
from components.personalization import (
    PersonalizationRepository,
    restore_adaptive_engine,
    persist_adaptive_engine,
)

# 1. Initialize repository
repo = PersonalizationRepository()

# 2. Restore engine from PostgreSQL for a given user
engine = restore_adaptive_engine(repo, user_id="user-001")
if engine is None:
    # First-time user: instantiate fresh engine
    engine = AdaptivePersonalizationEngine(user_id="user-001")

# 3. Perform recommendations and feedback processing
# ...

# 4. Persist updated engine state
persist_adaptive_engine(repo, engine, user_id="user-001")
```

### Authentication & User Boundaries
- User identity is currently caller-supplied (`user_id="user-001"`).
- Official authentication and JWT verification will be integrated in a subsequent milestone without altering the persistence schema.
