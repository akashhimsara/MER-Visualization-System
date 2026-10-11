
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

### Real DEAM Audio Validation

The early-exit implementation was additionally evaluated using
10 real DEAM audio windows from 10 distinct songs.

- TRAIN: 5 songs
- VALIDATION: 5 songs
- TEST: excluded
- Context: 5-second causal windows
- Sample rate: 24 kHz
- Compared representations: Layer 4 and Layer 8
- Total comparisons: 20
- Passed comparisons: 20/20
- Maximum observed absolute difference: 0.0

All tested real-audio embeddings matched the full MERT
implementation.

This supports numerical equivalence for the evaluated
samples, but does not establish equivalence across every
possible audio input.

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

## Safe Early-Exit Implementation

A second early-exit implementation was developed to avoid
temporarily replacing the encoder's forward method.

The safe implementation directly reuses the pretrained
feature extractor, feature projection, positional embeddings,
normalization, and the first eight transformer layers.

### Numerical Equivalence

Synthetic audio:
- Four signals tested
- Layer 4 and Layer 8 compared
- 8/8 comparisons passed
- Maximum observed absolute difference: 0.0

Real DEAM audio:
- Five TRAIN songs
- Five VALIDATION songs
- Twenty layer comparisons
- 20/20 comparisons passed
- TEST partition excluded

### Basic Concurrency Validation

Two concurrent inference requests were executed using the
same loaded model instance.

- Four embedding comparisons
- 4/4 comparisons passed
- Maximum observed absolute difference: 0.0

This is a limited concurrency correctness test, not proof
of production-level thread safety.

### Three-Way Latency Benchmark

Device: NVIDIA RTX 3050 Laptop GPU
Input: Synthetic 5-second waveform at 24 kHz
Warm-up: 20 iterations per measurement block
Measured iterations: 100 per block
Repetitions: 3

| Implementation | Mean (ms) | Mean P95 (ms) |
|---|---:|---:|
| Full MERT | 46.252 | 50.086 |
| Original early exit | 37.172 | 38.922 |
| Safe early exit | 38.538 | 39.812 |

The safe early-exit implementation reduced mean latency
by 16.68% relative to full MERT, corresponding to
approximately 1.20x speedup.

The P95 figures are averages of repetition-level P95
values rather than pooled P95 estimates.

The benchmark includes processor preparation, model
inference, and embedding pooling. It excludes audio
decoding, live capture, buffering, downstream regression,
and visualization.

### Research Decision

The safe early-exit implementation is selected for
subsequent integration
