# MERT Baseline Design v1

## Purpose

This experiment evaluates a frozen pretrained music representation
as an alternative to the traditional engineered-feature baseline for
continuous Valence-Arousal prediction on DEAM.

The selected pretrained model is:

m-a-p/MERT-v1-95M

MERT is used as a representation extractor. It is not treated as a
ready-made Valence-Arousal predictor.

---

## Prediction Task

Primary task:

Continuous multi-output emotion regression.

Targets:

- Valence
- Arousal

Separate lightweight regression heads are trained for the two targets.

Classification accuracy and F1 are not primary metrics for this experiment.

---

## Dataset and Split

Dataset:

DEAM dynamic Valence-Arousal annotations.

The canonical frozen song-level split is reused.

- TRAIN: model fitting
- VALIDATION: layer and regression configuration selection
- TEST: locked

No TEST results are used during MERT representation selection.

---

## Audio Context

Each target timestamp uses a causal 5-second audio context:

[t - 5 seconds, t]

No future audio relative to the target timestamp is included.

The 5-second context is retained for the initial experiment to provide
a controlled comparison with the traditional baseline.

Context-length optimization is deferred to the later temporal
experiments.

---

## Model-Native Preprocessing

MERT uses its native waveform-based preprocessing.

Audio is converted to mono and resampled to:

24,000 Hz

The original DEAM audio files are not permanently overwritten or
globally resampled.

The traditional baseline's 22,050 Hz analysis configuration does not
apply to MERT.

---

## Representation Extraction

Model:

m-a-p/MERT-v1-95M

Initial mode:

Frozen feature extractor.

Hidden size:

768 dimensions.

Candidate transformer representations:

- Layer 4
- Layer 8
- Layer 12

Layer selection is performed using the VALIDATION partition only.

The held-out TEST partition remains locked.

---

## Temporal Aggregation

Each MERT layer produces a sequence of hidden representations across
time.

For the initial controlled baseline, mean temporal pooling is used.

Therefore:

time_steps × 768

becomes:

1 × 768

for each target timestamp.

More complex temporal aggregation methods are outside this initial
baseline and may only be introduced later if experimentally justified.

---

## Regression Head

A lightweight Ridge regression model is used on top of the frozen
MERT representation.

Separate models are used for:

- Valence
- Arousal

Candidate Ridge alpha values:

- 0.01
- 0.1
- 1.0
- 10.0
- 100.0

Any feature scaling required by the regression stage must be fitted
using TRAIN data only.

---

## Evaluation Metrics

Valence and Arousal are evaluated separately using:

- MAE
- RMSE
- Pearson correlation
- Concordance Correlation Coefficient (CCC)
- R²

Model selection must not rely on a single metric alone.

---

## Controlled Comparison

The initial comparison is:

Traditional baseline:
5-second causal context
→ engineered audio features
→ 86-dimensional aggregated representation
→ Ridge regression

versus

Pretrained baseline:
5-second causal context
→ frozen MERT
→ 768-dimensional mean-pooled representation
→ Ridge regression

The comparison uses the same canonical DEAM song split and the same
continuous Valence-Arousal targets.

Model-native preprocessing is retained for each representation.

---

## Test Lock

The held-out TEST partition must not be evaluated during:

- candidate layer selection
- Ridge alpha selection
- representation selection
- temporal configuration selection
- optimization decisions

TEST evaluation is deferred until the final configuration has been
frozen.