# Traditional MER Baseline Design v1

## Purpose

This baseline provides an engineered-audio-feature reference for comparison
with pretrained and hybrid Music Emotion Recognition representations.

The primary task is continuous multi-output regression of Valence and Arousal.

## Target Source

Targets are taken from the canonical paired DEAM target manifest.

A target is usable only when both Valence and Arousal are valid at the same
song ID and timestamp.

The canonical song-level Train / Validation / Test split is preserved.

## Temporal Alignment

For the initial traditional baseline, each target at time t uses a causal
5.0-second audio context:

[t - 5.0 s, t]

Future audio after the target timestamp is not included.

The 5-second context is an initial controlled baseline configuration and is
not assumed to be globally optimal. Context-length sensitivity will be
evaluated separately during the temporal experiments.

## Initial Engineered Feature Families

The initial baseline will evaluate engineered audio descriptors including:

- MFCC
- Delta MFCC
- Chroma
- RMS energy
- Spectral centroid
- Spectral bandwidth
- Spectral rolloff
- Zero-crossing rate

Frame-level features will be temporally aggregated into fixed-dimensional
representations rather than flattened as raw frame sequences.

Initial aggregation statistics:

- Mean
- Standard deviation

Feature scaling parameters will be fitted using TRAIN data only.

## Audio Handling

Raw DEAM audio remains unchanged.

Feature extraction may use a controlled analysis sample rate for the
traditional branch. This does not define the preprocessing used by pretrained
models such as MERT, which retain their model-native frontend requirements.

Amplitude handling must preserve the distinction between engineered/model
preprocessing and the real-time Tier 1 RMS signal.

## Leakage Prevention

1. The frozen song-level split is applied before model fitting.
2. Windows from the same song cannot occur across different splits.
3. Feature scalers are fitted on TRAIN only.
4. Regressor fitting uses TRAIN only.
5. VALIDATION is used for model/configuration decisions.
6. TEST remains locked until final configuration freeze.

## Initial Output

Each usable sample will contain:

- song_id
- split
- target timestamp
- Valence target
- Arousal target
- engineered fixed-dimensional feature vector

## Evaluation

Valence and Arousal will be evaluated separately using the frozen regression
metrics:

- MAE
- RMSE
- Pearson correlation
- CCC
- R²

System measurements will be handled according to evaluation_protocol_v1.

## Frozen Initial Feature Extraction Configuration

The initial traditional baseline uses the following controlled configuration:

| Parameter | Value |
|---|---:|
| Audio context | 5.0 s causal |
| Analysis sample rate | 22,050 Hz |
| FFT size (`n_fft`) | 2048 |
| Hop length | 512 samples |
| MFCC coefficients | 13 |
| MFCC delta coefficients | 13 |
| Chroma bins | 12 |
| RMS | 1 |
| Spectral centroid | 1 |
| Spectral bandwidth | 1 |
| Spectral rolloff | 1 |
| Zero-crossing rate | 1 |
| Temporal aggregation | Mean + standard deviation |

The frame-level representation contains 43 feature dimensions:

13 MFCC + 13 delta MFCC + 12 chroma + 1 RMS + 1 spectral centroid +
1 spectral bandwidth + 1 spectral rolloff + 1 zero-crossing rate = 43.

Applying mean and standard-deviation aggregation to every dimension produces
an 86-dimensional fixed feature vector for each target timestamp.

The 22,050 Hz analysis rate applies only to the engineered-feature baseline.
It does not replace model-native preprocessing requirements of pretrained
models.

## Initial Regression Head

The first engineered-feature regression baseline uses Ridge Regression.

Separate regression models are fitted for Valence and Arousal. Feature
standardization is fitted on TRAIN only.

The initial regularization candidates are:

- 0.01
- 0.1
- 1.0
- 10.0
- 100.0

Candidate configurations are evaluated on VALIDATION only. The held-out TEST
partition remains locked.

Model selection is based on the complete continuous-regression evidence rather
than classification accuracy. Required validation metrics are MAE, RMSE,
Pearson correlation, CCC, and R² for Valence and Arousal separately.

This Ridge model is a controlled lightweight reference baseline and is not
assumed to be the globally optimal regressor.

## EXP_TRAD_001 Validation Selection

The initial Ridge candidate grid was evaluated using the frozen VALIDATION
partition only. The held-out TEST partition was not evaluated.

The selected target-specific regularization parameters are:

- Valence: alpha = 0.1
- Arousal: alpha = 100.0

Valence performance was effectively unchanged between the smallest candidate
values, while stronger regularization gradually reduced the validation
metrics. Alpha 0.1 was retained as the deterministic Valence configuration.

For Arousal, alpha 100.0 produced the strongest validation results among the
tested candidates across the reported regression metrics.

The selected parameters are validation-derived configuration choices and are
not final TEST results.