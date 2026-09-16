# Member 1 MER Research Protocol v1

## 1. Research Component

Music Emotion Recognition and Real-Time Audio Analysis for an
Emotion-Adaptive Real-Time Music Visualization System.

## 2. Main Research Question

Which combination of audio representation, pretrained music/audio model
configuration, and multi-tier temporal scheduling provides a suitable
trade-off between continuous Valence-Arousal prediction performance,
temporal responsiveness, inference latency, and computational resource
consumption for real-time emotion-adaptive music visualization?

## 3. Primary Machine Learning Task

The primary machine learning task is dynamic continuous
Valence-Arousal (VA) regression.

Input:
Music audio.

Primary outputs:
- Continuous Valence value
- Continuous Arousal value

Task type:
Multi-output regression.

Categorical emotion labels are not the primary prediction target.
If required by downstream visualization components, categorical emotion
states may later be derived from the predicted Valence-Arousal values
using a documented mapping.

## 4. Primary Dataset

The primary experimental dataset is DEAM
(Database for Emotional Analysis of Music).

Dynamic Valence-Arousal annotations will be used for the main
continuous emotion prediction experiments.

Before model training:
- Audio files and annotation files must be verified.
- Song IDs must be matched correctly.
- Dynamic annotation timestamps must be inspected.
- Audio windows must be correctly aligned with VA targets.
- A song-level Train / Validation / Test split must be created.

## 5. Data Split Policy

The dataset will be divided at song level into:

- Training set
- Validation set
- Held-out Test set

Windows or segments from the same song must never appear in different
partitions.

Training data:
Used to fit model parameters.

Validation data:
Used for model selection, hyperparameter selection, feature selection,
context-length selection, hop/update-interval selection, and optimization
decisions.

Test data:
Reserved exclusively for final evaluation after all design decisions
have been frozen.

The held-out test set must not be used to make modelling or optimization
decisions.

## 6. Experimental Configuration Families

### E1 - Traditional Engineered-Feature Baseline

Candidate engineered features include:
- MFCC
- Chroma
- Spectral descriptors
- RMS energy
- Onset-related features
- Tempo/rhythmic information where appropriate

These features will be represented using a documented temporal
aggregation strategy and used with lightweight regression models.

### E2 - Pretrained Music Representation

A selected pretrained music/audio representation model, initially MERT,
will be investigated using its model-native preprocessing requirements.

Learned embeddings will be extracted and evaluated using a lightweight
Valence-Arousal regression head.

### E3 - Hybrid Representation

Selected learned embeddings will be combined with selected engineered
audio features.

The hybrid configuration will be compared with E1 and E2 under the same
experimental protocol.

### E4 - Controlled Adaptation

Controlled adaptation or fine-tuning will only be performed if validation
evidence shows that it is scientifically justified and computationally
feasible.

## 7. Affective Evaluation Metrics

Valence and Arousal will be evaluated separately.

Primary affective metrics:

- Mean Absolute Error (MAE)
- Root Mean Square Error (RMSE)
- Pearson Correlation Coefficient (r)
- Concordance Correlation Coefficient (CCC)
- Coefficient of Determination (R²)

Accuracy, Precision, Recall and F1-score are not primary metrics because
the primary research task is continuous regression rather than
classification.

## 8. Real-Time / Computational Metrics

Candidate configurations will also be evaluated using:

- Mean inference latency (ms)
- P95 inference latency (ms)
- Average CPU utilization (%)
- Peak CPU utilization (%)
- Peak memory usage (MB)
- Throughput / real-time processing capability
- End-to-end pipeline delay where applicable

Model inference latency and complete pipeline delay must be reported
separately.

## 9. Multi-Tier Processing Contract

### Tier 1 - Lightweight Acoustic Analysis

Purpose:
Provide rapid low-level information for immediate visual responsiveness.

Candidate outputs:
- timestamp
- RMS energy
- spectral centroid
- onset detection
- onset strength

Initial target refresh interval:
Approximately 0.1 seconds.

This value is an initial engineering target and is subject to experimental
validation.

### Tier 2 - Rhythmic / Tempo Analysis

Purpose:
Provide slower-changing rhythmic context.

Candidate outputs:
- timestamp
- tempo / BPM

Initial target refresh interval:
Approximately 2-3 seconds.

Tempo estimation may use a rolling audio context longer than its output
refresh interval.

This value is an initial engineering target and is subject to experimental
validation.

### Tier 3 - Emotion Estimation

Purpose:
Provide higher-level continuous musical emotion information.

Mandatory outputs:
- timestamp
- valence
- arousal

Initial target prediction refresh interval:
Approximately 1 second.

The Tier 3 audio context length and prediction update interval are
independent experimental variables and will be determined experimentally.

## 10. Temporal Experiment Rule

The following quantities must never be treated as equivalent:

1. Audio context/window length
2. Hop/update interval
3. Preprocessing latency
4. Model inference latency
5. End-to-end pipeline delay

Example:

A model may use a 5-second audio context, produce a new prediction every
1 second, and require only 120 ms to perform inference.

Context length and update interval will therefore be evaluated as
independent experimental variables.

## 11. Model Selection Rule

No final model will be selected using a single metric alone.

Candidate configurations will be compared using the trade-off among:

- Valence-Arousal prediction quality
- Temporal responsiveness
- Inference latency
- CPU utilization
- Memory utilization
- Computational efficiency

Pareto-relevant configurations will be prioritized for further
optimization.

## 12. Reproducibility Rule

Every experiment must record:

- Experiment ID
- Date
- Dataset version
- Split version
- Model / representation
- Audio context length
- Hop / update interval
- Random seed
- Hyperparameters
- Affective metrics
- System-performance metrics
- Hardware
- Software environment
- Code / commit version
- Decision or conclusion

## 13. Scope Boundary

This individual component is responsible for:

- Music Emotion Recognition
- Audio feature analysis
- Tempo/rhythmic analysis
- Multi-tier audio processing
- Timestamped structured outputs
- MER performance evaluation
- MER computational optimization
- Integration interface for downstream components

This component is not responsible for:

- Designing emotion-to-visual mappings
- Rendering final visualizations
- Determining visual transition behaviour
- User-personalization algorithms

Those responsibilities belong to the other research components.

## 14. Protocol Freeze Rule

Once this protocol is accepted for experimentation, major changes to the
dataset split, primary target, evaluation metrics, or final test procedure
must be documented and justified.

The held-out test set will remain locked until the final experimental
configuration has been selected and frozen.