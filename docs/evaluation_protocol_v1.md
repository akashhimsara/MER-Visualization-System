# Member 1 MER Evaluation Protocol v1

## 1. Purpose

This document defines the fixed evaluation procedure for all Music Emotion
Recognition experiments conducted in the Member 1 research component.

The purpose is to ensure that traditional, pretrained, hybrid, adapted and
optimized configurations are evaluated fairly under consistent conditions.

---

## 2. Primary Prediction Task

The primary task is continuous Valence-Arousal regression.

Each prediction contains:

- Predicted Valence
- Predicted Arousal

Valence and Arousal must be evaluated separately.

Classification Accuracy, Precision, Recall and F1-score are not primary
evaluation metrics.

---

## 3. Affective Prediction Metrics

For every model configuration, calculate the following separately for
Valence and Arousal.

### 3.1 Mean Absolute Error (MAE)

Measures the average absolute difference between predicted and ground-truth
values.

Interpretation:

Lower MAE = better prediction performance.

### 3.2 Root Mean Square Error (RMSE)

Measures prediction error while penalizing larger errors more strongly
than MAE.

Interpretation:

Lower RMSE = better prediction performance.

### 3.3 Pearson Correlation Coefficient (r)

Measures the linear relationship between predicted and ground-truth
emotion trajectories.

Interpretation:

Higher positive correlation = better tracking of emotional variation.

### 3.4 Concordance Correlation Coefficient (CCC)

Measures agreement between predictions and ground truth by considering
both correlation and deviation from the identity line.

Interpretation:

Higher CCC = better agreement.

### 3.5 Coefficient of Determination (R²)

Measures how much variation in the ground-truth values is explained by
the model.

Interpretation:

Higher R² = better explanatory prediction performance.

A negative R² value is possible and must not be removed or hidden.

---

## 4. Required Affective Results

Each experiment must report:

| Metric | Valence | Arousal |
|---|---:|---:|
| MAE | value | value |
| RMSE | value | value |
| Pearson r | value | value |
| CCC | value | value |
| R² | value | value |

No experiment may be declared the final configuration using only one
of these metrics.

---

## 5. Dataset Evaluation Policy

The dataset is separated at song level into:

TRAIN
VALIDATION
TEST

TRAIN:
Used to fit model parameters.

VALIDATION:
Used for all experimental decisions including:

- model selection
- feature selection
- hyperparameter selection
- context-length selection
- hop/update-interval selection
- hybrid configuration selection
- optimization selection

TEST:
Used only for the final locked evaluation.

Test-set results must not be used to select or modify a configuration.

---

## 6. Computational Performance Metrics

The following system metrics will be measured for relevant candidate
configurations.

### 6.1 Mean Inference Latency

Average time required for the model inference operation.

Unit:
milliseconds (ms)

### 6.2 P95 Inference Latency

95th percentile inference latency.

This is included because mean latency alone may hide occasional slow
inference operations.

Unit:
milliseconds (ms)

### 6.3 CPU Utilization

Record where applicable:

- Average CPU utilization (%)
- Peak CPU utilization (%)

### 6.4 Memory Utilization

Record peak process memory consumption where applicable.

Unit:
MB

### 6.5 Throughput / Real-Time Capability

Determine whether processing can keep up with the required update
schedule during continuous operation.

The system must not develop an indefinitely growing processing backlog.

---

## 7. Timing Definitions

The following quantities must be measured or documented separately.

### Audio Context Length

Amount of audio used to produce one estimate.

Example:
5 seconds.

### Hop / Update Interval

Time between successive predictions.

Example:
1 second.

### Preprocessing Latency

Time required to transform raw audio into the representation required by
the model.

### Model Inference Latency

Time spent executing the prediction model.

### End-to-End Pipeline Delay

Total relevant delay from available audio input to usable downstream
output.

These quantities must not be treated as equivalent.

---

## 8. Latency Measurement Procedure

For each configuration selected for system profiling:

1. Use the same documented hardware.
2. Use the same relevant software environment.
3. Perform warm-up executions before measurement.
4. Exclude warm-up executions from reported measurements.
5. Measure multiple inference executions.
6. Record individual inference times.
7. Calculate mean latency.
8. Calculate P95 latency.
9. Record CPU and memory measurements where applicable.
10. Record context length and update interval separately.

The number of repeated measurements used in the final benchmark will be
fixed before final testing.

---

## 9. Fair Comparison Rules

When comparing candidate configurations:

- Use the same song-level dataset split.
- Use equivalent target definitions.
- Prevent song-level leakage.
- Use model-native preprocessing where required.
- Do not force every pretrained model to use the same sample rate if its
  native preprocessing requires a different sample rate.
- Run computational benchmarks on the same reference hardware.
- Record software versions.
- Record random seeds where applicable.
- Repeat timing measurements.
- Do not selectively report only favourable results.

---

## 10. Model Selection Strategy

The final configuration will not be selected solely because it has the
lowest prediction error.

Selection will consider the joint trade-off among:

- MAE
- RMSE
- Pearson r
- CCC
- R²
- Mean inference latency
- P95 inference latency
- CPU utilization
- Memory utilization
- Real-time processing capability

Pareto-relevant configurations will be prioritized.

Example:

If Model A provides a very small prediction-quality improvement but is
substantially slower and consumes substantially more resources than
Model B, both results will be reported and the practical trade-off will
be analyzed rather than declaring Model A automatically superior.

---

## 11. Tier-Specific Evaluation

### Tier 1

Evaluate:

- update sustainability
- processing latency
- CPU utilization
- memory behavior
- onset output behavior where applicable

Initial target refresh:
approximately 0.1 seconds.

### Tier 2

Evaluate:

- tempo estimation behavior
- refresh sustainability
- processing latency
- CPU utilization
- memory behavior

Initial target refresh:
approximately 2-3 seconds.

Tempo estimation context length may be longer than the refresh interval.

### Tier 3

Evaluate:

- Valence-Arousal prediction quality
- context-length effect
- update-interval effect
- inference latency
- CPU utilization
- memory utilization
- continuous processing sustainability

Initial target refresh:
approximately 1 second.

The final Tier 3 context length and update interval will be determined
experimentally.

---

## 12. Final Test Lock

The held-out test set may be evaluated only after the following are frozen:

- final candidate model/configuration
- input representation
- preprocessing procedure
- feature set
- hyperparameters
- context length
- hop/update interval
- optimization method
- evaluation code
- software environment

If any of these are changed after viewing test results, the change must be
documented and the test result must not be represented as an untouched
final evaluation.

---

## 13. Reporting Rule

Both successful and unsuccessful experiments that materially affect a
research decision must be documented.

Every reported comparison must identify:

- Experiment ID
- Dataset/split version
- Model/configuration
- Representation
- Context length
- Hop/update interval
- Random seed where applicable
- Affective metrics
- Computational metrics where applicable
- Hardware
- Software/code version
- Decision/conclusion