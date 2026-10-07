# Shared Contracts

**Contract Version:** 1.1
**Schema Standard:** JSON Schema Draft 2020-12

This directory defines the shared integration interfaces used by the four research components of the Emotion-Adaptive Real-Time Music Visualization System.

The contracts define **how components communicate**, not how each component is internally implemented.

A component may change its internal model, algorithm, or implementation as long as its externally shared messages remain compatible with the agreed contracts.

## Contract Set

Contract v1.1 will define the following shared interfaces:

| Contract          | Primary Producer / Owner    | Main Consumers                             |
| ----------------- | --------------------------- | ------------------------------------------ |
| MER Tier 1        | Music Emotion Recognition   | Visualization, Transition                  |
| MER Tier 2        | Music Emotion Recognition   | Visualization, Transition                  |
| MER Tier 3        | Music Emotion Recognition   | Visualization, Transition, Personalization |
| VisualPreset      | Visualization               | Personalization, Renderer                  |
| Recommendation    | Personalization             | Visualization                              |
| TargetVisualState | Visualization               | Transition, Renderer                       |
| TransitionCommand | Transition                  | Renderer                                   |
| FeedbackEvent     | Frontend / User Interaction | Personalization                            |

## Canonical Emotion Representation

Cross-component emotion communication uses continuous **Valence-Arousal (VA)** values.

```text
Valence: -1.0 to +1.0
Arousal: -1.0 to +1.0
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

## Real-Time Event Envelope

Real-time contracts use a common set of metadata fields:

```text
schema_version
event_type
session_id
sequence
audio_time_ms
```

`audio_time_ms` represents elapsed time from the beginning of the current audio/session in milliseconds.

It is not a wall-clock timestamp.

## Component Boundaries

### Music Emotion Recognition

Owns:

- Tier 1 acoustic outputs
- Tier 2 tempo/rhythmic outputs
- Tier 3 continuous Valence-Arousal outputs

The MER component does not define visual mappings or transition behaviour.

### Visualization

Owns:

- Visual presets
- Emotion-to-visual mapping
- Target visual states
- Three.js rendering parameters

The visualization component does not decide transition timing.

### Transition System

Owns:

- Transition decisions
- Transition timing
- Transition duration
- Transition strength
- Temporal continuity logic

The transition component references a target visual state rather than redesigning the visual state itself.

### Personalization

Owns:

- Visualization recommendations
- Preference learning
- Feedback processing
- Recommendation strategy

The personalization component recommends a stable `preset_id` rather than directly controlling low-level Three.js parameters.

## Visual Preset Stability

`preset_id` values should remain stable once personalization experiments begin.

A preset represents a reusable visualization configuration that may be treated as a recommendation option by the personalization component.

## Confidence Values

Confidence values must only be provided when they have a meaningful interpretation.

A component must not fabricate confidence values only to satisfy an interface.

Where supported by the schema, unavailable confidence values should be represented as `null`.

## Authentication Boundary

Client-generated feedback must not be trusted to provide an authoritative user identity.

When authentication is implemented, the backend will derive the user identity from the authenticated session or JWT.

## Versioning

The current shared contract version is:

```text
1.1
```

Do not silently:

- rename existing fields
- remove existing fields
- change field meanings
- change units
- change numeric ranges
- change required/optional behaviour

Breaking changes require:

1. Discussion with affected team members
2. Schema update
3. Example update
4. Validation
5. New contract version when necessary

## Validation

Each JSON example must validate successfully against its corresponding JSON Schema.

The automatic Contract v1.1 validator will be added in the next implementation step.

## Source of Truth

Files inside:

```text
contracts/schemas/
```

are the source of truth for cross-component message structure.

Files inside:

```text
contracts/examples/
```

provide valid example messages for documentation, testing, mocks, and independent component development.

Research documents may describe expected outputs, but if a research document and a shared integration schema differ, the agreed versioned schema should be used for system integration.
