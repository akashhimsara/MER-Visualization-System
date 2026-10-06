# Contracts

## Contract versioning

Shared interfaces are versioned.

Breaking changes require agreement from affected team members.

## Canonical emotion representation

Cross-component emotion communication uses continuous:

```text
Valence
Arousal
```

Categorical values such as:

```text
HAPPY
SAD
CALM
ENERGETIC
TENSE
EXCITED
```

must not be used as the primary cross-component emotion representation.

Individual components may derive such labels internally.

## Component isolation

Internal implementation may change as long as shared contracts remain compatible.

The full Contract v1.1 schemas will later define:

```text
MER Tier 1
MER Tier 2
MER Tier 3
VisualPreset
Recommendation
TargetVisualState
TransitionCommand
FeedbackEvent
```
