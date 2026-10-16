# T4.5 — Frozen Model Shortlist for Temporal Experiments

## Objective

Freeze the model configurations selected from Phase P4 for controlled temporal evaluation in Phase P5.

## Selection Basis

Models were compared using TRAIN-fitted estimators, VALIDATION performance, and controlled prepared-window latency measurements.

The held-out TEST partition has not been evaluated.

## Frozen Shortlist

### Candidate 1 — Primary Latency-Oriented Model

**Frozen MERT-v1-95M + Safe Early Exit + Ridge Regression**

- MERT checkpoint: `m-a-p/MERT-v1-95M`
- Input: 5-second causal mono audio window
- Native sample rate: 24,000 Hz
- Early-exit layer: 8
- Valence: Layer 4 embeddings, Ridge alpha 100
- Arousal: Layer 8 embeddings, Ridge alpha 100
- Embedding dimension: 768 per target
- Model weights: frozen
- Validation MAE: Valence 0.183636; Arousal 0.136370
- Controlled mean prepared-window inference latency: 32.308 ms

### Candidate 2 — Accuracy-Oriented Comparison

**Traditional Features + Frozen MERT Embeddings + Ridge Regression**

- Input: aligned 5-second causal audio context
- Traditional sample rate: 22,050 Hz
- MERT sample rate: 24,000 Hz
- Traditional features: 86D
- MERT embeddings: 768D
- Combined features: 854D
- Valence: MERT Layer 4 + Traditional, Ridge alpha 100
- Arousal: MERT Layer 8 + Traditional, Ridge alpha 100
- Validation MAE: Valence 0.181762; Arousal 0.135393
- Controlled mean prepared-window inference latency: 69.259 ms

### Candidate 3 — Reference Baseline

**Traditional Engineered Features + Ridge Regression**

- Input: 5-second causal audio window at 22,050 Hz
- Feature dimension: 86D
- Valence Ridge alpha: 0.1
- Arousal Ridge alpha: 100
- Validation MAE: Valence 0.208435; Arousal 0.156690
- Controlled mean prepared-window inference latency: 51.290 ms

## Freeze Rules

1. Do not change pretrained weights, feature definitions, selected layers, Ridge hyperparameters, or TRAIN-fitted scalers during temporal comparisons.
2. Keep the existing song-level TRAIN, VALIDATION, and TEST partition assignments unchanged.
3. Use the same temporal evaluation protocol across shortlisted candidates.
4. Treat the selected models as provisional until the final evaluation stage.
5. Do not access the TEST partition during temporal development.
6. Record any future model or preprocessing modification as a new experiment version rather than silently replacing frozen artifacts.

## Phase P5 Entry Decision

The frozen MERT-only candidate is the primary latency-oriented model.

The hybrid candidate is retained to examine whether its modest validation accuracy advantage persists under temporal evaluation.

The traditional baseline is retained as a reference.

**Status: T4.5 shortlist frozen at the configuration level, pending artifact integrity verification.**