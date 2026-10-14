# T4.3 — Hybrid MER Ablation and Controlled Comparison

## Experiment Scope

This experiment compares three Music Emotion Recognition approaches:

1. Traditional engineered audio features with Ridge regression.
2. Frozen pretrained MERT embeddings with Ridge regression.
3. Hybrid concatenation of traditional features and MERT embeddings with Ridge regression.

All predictive models were trained on the TRAIN partition and selected using VALIDATION results. The TEST partition remained locked.

## Validation Performance

| Model | Valence MAE | Arousal MAE |
|---|---:|---:|
| Traditional | 0.208435 | 0.156690 |
| MERT-only | 0.183636 | 0.136370 |
| Hybrid | 0.181762 | 0.135393 |

The hybrid approach achieved the lowest validation MAE for both targets. Compared with MERT-only, its relative MAE improvements were approximately 1.02% for valence and 0.72% for arousal.

These are modest improvements and have not yet been evaluated for statistical significance or generalization to the held-out TEST partition.

## Controlled Prepared-Window Latency

The three approaches were benchmarked using the same five-second TRAIN audio interval from DEAM song 2, on the same machine. Each approach was measured across three repetitions of 50 runs, following warmup.

Audio decoding, resampling, live capture, buffering, network communication, and visualization were excluded from timed inference.

| Model | Mean (ms) | Median (ms) | P95 (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|
| Traditional | 51.290 | 35.261 | 143.398 | 360.316 |
| MERT-only | 32.308 | 32.222 | 33.322 | 35.749 |
| Hybrid | 69.259 | 67.431 | 79.858 | 105.493 |

P95 values were calculated from the pooled 150 measurements per model.

The MERT-only approach demonstrated the lowest mean latency and the most consistent measured inference times. The traditional approach exhibited substantial latency outliers, particularly during the first repetition.

## Benchmark Integrity

- Total measurements: 450.
- Measurements per model: 150.
- Missing values: 0.
- Non-finite predictions: 0.
- TEST partition accessed: No.
- Benchmark audit: PASS.

## Interpretation

The hybrid model provided the strongest validation MAE but required approximately 36.951 ms more mean inference time than MERT-only under the controlled benchmark.

This corresponds to approximately 2.14 times the MERT-only mean latency.

The observed accuracy improvement is small relative to the additional computational cost.

## Provisional Research Decision

Retain the frozen MERT-only model with safe early-exit inference as the provisional latency-oriented candidate for subsequent temporal experiments.

Retain the hybrid model as the accuracy-oriented comparison candidate.

Do not interpret this as final model selection. Further evaluation is required across multiple audio windows, temporal configurations, complete system latency, and the held-out TEST partition at the appropriate final evaluation stage.

## Limitations

- Latency was measured repeatedly on one TRAIN audio interval.
- The benchmark did not include the complete real-time audio-to-visualization pipeline.
- Traditional feature extraction showed substantial timing variability.
- GPU and CPU processing costs differ across pipeline stages.
- Validation improvements have not been tested for statistical significance.
- No TEST results were used.

## Evidence

- `outputs/results/EXP_TRAD_001_validation.csv`
- `outputs/results/EXP_MERT_001_validation.csv`
- `outputs/results/EXP_HYBRID_001_validation.csv`
- `outputs/results/EXP_HYBRID_001_controlled_comparison.csv`

**Status:** T4.3 benchmark evidence documented; provisional interpretation pending broader validation.