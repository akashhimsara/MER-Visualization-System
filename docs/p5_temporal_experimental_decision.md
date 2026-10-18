# Temporal MER Experiments — Experimental Decision

## Objective

Evaluate temporal context length, prediction refresh interval, smoothing, inference latency, and scheduling feasibility for continuous Valence–Arousal Music Emotion Recognition.

All model-selection experiments use the DEAM TRAIN and VALIDATION partitions. The TEST partition remains locked.

## Experimental Findings

### 1. Context Length

Frozen MERT embeddings were evaluated using 3-second, 5-second, and 8-second causal audio contexts.

| Context | Valence MAE | Arousal MAE |
|---|---:|---:|
| 3 seconds | 0.185967 | 0.138200 |
| 5 seconds | 0.183636 | 0.136370 |
| 8 seconds | 0.179860 | 0.135728 |

The 8-second context produced the lowest pooled validation MAE, but increased inference cost. The selected valence layer also differed between configurations, so the comparison does not isolate context length alone.

Song-level paired bootstrap comparisons did not establish a clear improvement of 8 seconds over 5 seconds for either target at the 95% confidence interval level.

**Decision:** Retain the 5-second context as the primary implementation candidate. Keep the 8-second configuration as an accuracy-oriented alternative.

### 2. Temporal Refresh Interval

The 5-second MERT model was evaluated at refresh intervals of 0.5, 1, and 2 seconds.

A causal hold-last-value comparison evaluated all configurations against the same 19,965 VALIDATION timestamps across 270 songs.

| Hop | Valence MAE | Arousal MAE |
|---|---:|---:|
| 0.5 seconds | 0.183636 | 0.136370 |
| 1 second | 0.183319 | 0.136065 |
| 2 seconds | 0.183765 | 0.135647 |

The differences were small. Song-level paired bootstrap analysis did not establish consistent superiority of the 1-second interval.

One exploratory comparison, arousal song-level RMSE for 1 second versus 2 seconds, had a confidence interval excluding zero in favor of 2 seconds. This result should be interpreted cautiously because multiple comparisons were examined.

### 3. Scheduling and Computational Cost

A five-song TRAIN benchmark measured prepared-window inference latency using the frozen MERT model and Ridge predictors.

| Hop | Mean latency | P95 latency | Nominal inference workload per audio minute |
|---|---:|---:|---:|
| 0.5 seconds | 64.15 ms | 123.66 ms | 7.70 seconds |
| 1 second | 86.39 ms | 143.43 ms | 5.18 seconds |
| 2 seconds | 76.40 ms | 81.97 ms | 2.29 seconds |

The offline serial scheduling simulation reported zero completion deadline misses and zero queue waiting across all 450 measured predictions.

These findings do not establish full end-to-end real-time performance. Audio capture, decoding, concurrent processing tiers, network communication, and visualization overhead were not included.

### 4. Temporal Stability and Responsiveness

Causal hold-last-value evaluation reduced the frequency of prediction changes as the refresh interval increased.

The 2-second interval produced the lowest change MAE, but this can partly result from holding predictions constant when ground-truth changes are small. It does not demonstrate faster or more accurate tracking of emotional transitions.

Measured mean scheduled update age was approximately:

- 0.5 seconds: 0 ms
- 1 second: 253 ms
- 2 seconds: 760 ms

These values exclude inference completion and communication delays.

### 5. Temporal Smoothing

Exploratory causal exponential moving average (EMA) smoothing improved validation MAE at alpha = 0.2 compared with unsmoothed predictions.

However, smoothing can introduce response lag. The existing lag analysis was exploratory and did not establish a reliable physical response-delay estimate.

**Decision:** Retain EMA smoothing as an optional configuration, not a mandatory finalized processing step.

## Provisional Implementation Configuration

| Component | Candidate |
|---|---|
| Audio context | 5 seconds, causal |
| Tier 3 refresh interval | 1 second |
| Feature backbone | Frozen MERT-v1-95M |
| Valence predictor | MERT layer 4 + Ridge |
| Arousal predictor | MERT layer 8 + Ridge |
| Smoothing | Optional causal EMA |
| Model status | Provisional; not final freeze |

The 1-second refresh interval is selected as a practical engineering compromise between update freshness and computational workload, **not because it was statistically proven to have the best prediction accuracy**.

## Limitations and Next Validation

Further work must evaluate runtime optimization, resource usage, concurrent multi-tier processing, actual end-to-end latency, and integration behavior.

No final TEST evaluation has been performed. The TEST partition must remain locked until the model and evaluation configuration are frozen.
