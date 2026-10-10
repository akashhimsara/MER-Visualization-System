
# MERT Early-Exit Optimization — EXP_MERT_001

## Objective
Reduce pretrained MERT inference latency while preserving
the selected Layer 4 valence and Layer 8 arousal embeddings.

## Method
- Backbone: m-a-p/MERT-v1-95M
- Original encoder depth: 12 transformer layers
- Early-exit depth: 8 transformer layers
- Skipped layers: 9–12
- Pretrained weights: unchanged
- Model mode: evaluation
- Hardware: NVIDIA RTX 3050 Laptop GPU
- Input: synthetic 5-second mono audio at 24 kHz
- Benchmark: 3 repetitions, 100 measured iterations per mode
- Warmup: 20 iterations per mode

## Numerical Equivalence
Five synthetic audio inputs were evaluated.

- Layer 4: exact numerical agreement in tested inputs
- Layer 8: exact numerical agreement in tested inputs
- Total checks: 10/10 PASS
- DEAM TEST partition: not used

## Performance Results

| Repetition | Full Mean (ms) | Early Mean (ms) |
|---|---:|---:|
| 1 | 42.264 | 34.782 |
| 2 | 44.242 | 35.648 |
| 3 | 43.539 | 34.437 |
| Average | 43.348 | 34.956 |

Mean latency reduction: 19.36%
Speedup: 1.24x

All three repetitions showed lower mean and P95 latency
for the early-exit implementation.

## Measurement Scope
Includes processor, MERT forward execution and
embedding extraction.

Excludes audio capture, decoding, buffering,
Ridge predictions and visualization rendering.

## Limitations
- Synthetic audio inputs only
- Numerical equivalence tested on five inputs
- Single GPU hardware configuration
- Early-exit implementation temporarily replaces
  encoder.forward and is not concurrency-safe
- Complete end-to-end real-time performance not established
- DEAM TEST remains locked

## Status
Research prototype validated for numerical equivalence
and preliminary latency improvement.

Production-safe implementation and broader evaluation
remain pending.
