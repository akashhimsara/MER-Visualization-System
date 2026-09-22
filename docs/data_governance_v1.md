# Member 1 MER Data Governance Protocol v1

## 1. Purpose

This document defines the fixed rules governing dataset preparation,
data splitting, target alignment, leakage prevention, and held-out test
usage for the Member 1 Music Emotion Recognition experiments.

These rules must be established before formal model experiments begin.

---

## 2. Primary Dataset

Primary dataset:

DEAM - Database for Emotional Analysis of Music

Primary prediction targets:

- Continuous Valence
- Continuous Arousal

Dynamic annotations will be used for the primary MER experiments.

---

## 3. Experimental Unit

The song is the primary unit used for dataset partitioning.

Audio windows extracted from the same song must not be distributed
across training, validation, and test partitions.

Therefore:

TRAIN songs
VALIDATION songs
TEST songs

must be mutually exclusive.

---

## 4. Leakage Prevention

Dataset splitting must occur at SONG LEVEL before experimental audio
windows are generated.

Forbidden:

1. Randomly splitting extracted windows into train, validation and test.
2. Allowing windows from one song to appear in multiple partitions.
3. Fitting feature scalers using validation or test data.
4. Selecting features using test-set performance.
5. Selecting model hyperparameters using test-set performance.
6. Selecting temporal context or hop settings using test-set results.
7. Using the test set repeatedly during model development.

Any normalization or transformation requiring fitted statistics must be
fit using TRAIN data only.

The fitted transformation may then be applied unchanged to validation
and test data.

---

## 5. Dataset Split Policy

One canonical song-level split will be generated and saved under:

data/splits/

The split must be reproducible using the project's fixed random seed.

Primary split seed:

42

The generated split manifest must explicitly record the song IDs
belonging to:

- TRAIN
- VALIDATION
- TEST

The same canonical split must be reused across the traditional,
pretrained, hybrid and temporal experiments whenever scientifically
compatible.

The exact split proportions will be finalized during DEAM data
integrity analysis before the split manifest is generated.

Once the canonical split is generated and verified, it must not be
silently regenerated.

Any justified change requires a new split version.

---

## 6. Held-Out Test Lock

The TEST partition is a locked held-out evaluation set.

During model development:

TRAIN:
Used for fitting model parameters.

VALIDATION:
Used for model selection, feature selection, hyperparameter selection,
representation selection, context-length selection, hop selection and
optimization decisions.

TEST:
Not used for those decisions.

The held-out TEST partition will only be evaluated after the final
experimental configuration has been frozen.

---

## 7. Dynamic Annotation Alignment

DEAM dynamic Valence-Arousal annotations must be aligned with audio
using their documented annotation timestamps.

Target alignment must not be based only on CSV row numbers.

The first annotated timestamp and annotation interval must be verified
against the DEAM files before formal preprocessing.

For every generated training example, the relationship between:

- song ID
- audio start time
- audio end time
- target timestamp or target interval
- Valence target
- Arousal target

must be recoverable.

The final window-to-target aggregation rule will be determined and
documented during the DEAM integrity and preprocessing phase.

---

## 8. Audio Processing Policy

Raw source audio must remain unchanged.

Derived/resampled audio or features must be stored separately.

Traditional engineered-feature processing and pretrained-model
processing may use different model-appropriate sample rates.

MERT processing will follow its native preprocessing requirements,
including 24 kHz input.

No global resampling rule will be imposed solely to make all branches
identical.

---

## 9. RMS and Amplitude Policy

Amplitude-related processing must be treated carefully because RMS
energy is part of the real-time Tier 1 output.

Waveform normalization required by a specific model must not be confused
with visualization-oriented or engineered RMS measurements.

Any amplitude normalization that changes the interpretation of RMS must
be explicitly documented.

---

## 10. Dataset Versioning

Processed datasets must have identifiable versions.

A dataset version must record at minimum:

- source dataset
- preprocessing version
- split version
- sample-rate policy
- window/context configuration where applicable
- target-alignment method

Processed data must not silently overwrite a previously used
experimental dataset version.

---

## 11. Experiment Traceability

Every formal experiment must be traceable to:

Experiment ID
    ↓
Git commit
    ↓
Dataset version
    ↓
Split version
    ↓
Model/configuration
    ↓
Evaluation results

An experimental result without sufficient traceability must not be used
as final dissertation evidence.

---

## 12. Change-Control Rule

After the canonical split and preprocessing protocol are frozen, any
material change must be documented.

Examples:

- changing split proportions
- changing song assignments
- changing target alignment
- changing preprocessing
- changing sample-rate policy
- changing window generation logic

A justified material change requires a new version rather than silently
modifying the previous configuration.

---

## 13. Current Freeze Status

Research task:
Continuous Valence-Arousal regression.

Primary dataset:
DEAM.

Split unit:
Song.

Primary random seed:
42.

Test policy:
Locked held-out test set.

Exact split proportions:
Not yet frozen.

Exact temporal target aggregation:
Not yet frozen.

Reason:

These two decisions require verified DEAM data-integrity evidence and
will be finalized during Phase 1 before model training.