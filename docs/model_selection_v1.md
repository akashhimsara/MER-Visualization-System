# Pretrained Model Selection Protocol v1

## Primary Candidate

Model:
m-a-p/MERT-v1-95M

Role:
Pretrained music representation extractor for continuous
Valence-Arousal regression.

The pretrained model is not treated as a ready-made Valence-Arousal
predictor. Learned MERT representations will be extracted and evaluated
using a downstream lightweight regression model.

## Model Characteristics

Approximate parameter count:
95 million

Transformer structure:
12 hidden Transformer layers

Hidden representation dimension:
768

Native audio sample rate:
24,000 Hz

Pretraining context:
5 seconds

Feature rate:
Approximately 75 Hz

## Preprocessing Rule

MERT input will follow the model-native preprocessing configuration.

Audio supplied to the MERT branch will therefore be resampled to
24,000 Hz where required.

The project will not arbitrarily force MERT to use the same sample rate
as the traditional engineered-feature branch.

The corresponding model feature extractor will be used rather than
manually replacing the model frontend with MFCC or Mel features.

## Representation Strategy

Initial experiments will use MERT as a frozen representation extractor.

Hidden representations will be extracted from the pretrained model.

Candidate layer representations and temporal aggregation strategies may
be compared using validation data.

A lightweight downstream regressor will map the selected representation
to:

- Valence
- Arousal

Fine-tuning of the pretrained backbone is not part of the initial MERT
baseline and will only be considered later if justified by experimental
evidence and available computational resources.

## Hardware Feasibility

Reference GPU:
NVIDIA GeForce RTX 3050 Laptop GPU

Available GPU memory:
approximately 6 GB

Because the available GPU memory is limited, MERT-v1-95M is selected as
the primary pretrained candidate instead of beginning with the
substantially larger MERT-v1-330M model.

Frozen embedding extraction will be attempted before any full or partial
backbone fine-tuning.

Batch size will be selected according to measured GPU memory behavior.

## License

The current m-a-p/MERT-v1-95M Hugging Face repository identifies the
model license as CC-BY-NC-4.0.

The checkpoint will therefore be used for academic/non-commercial
research under the applicable license terms.

Any future commercial deployment would require a separate licensing
review and must not assume that this research checkpoint is suitable for
commercial redistribution or use.

## Research Comparison Role

MERT-v1-95M will be compared against:

1. A traditional engineered-feature Valence-Arousal baseline.
2. A hybrid configuration combining selected MERT representations with
   selected engineered audio features.

All comparisons will use the same leakage-safe song-level data split and
compatible Valence-Arousal target definitions.

## Second Pretrained Candidate

A second pretrained candidate is optional rather than mandatory.

It will only be added if:

- it is technically compatible with the research task,
- its preprocessing requirements can be reproduced,
- licensing permits the intended academic use,
- available hardware can execute it,
- and adding it provides a meaningful scientific comparison.

The second candidate will not be added merely to increase the number of
models.

## Decision

Primary pretrained representation:
MERT-v1-95M

Initial use:
Frozen representation extraction.

Primary downstream task:
Continuous Valence-Arousal regression.

Native MERT sample rate:
24 kHz.

Final context length:
Not frozen at this stage.

Final update interval:
Not frozen at this stage.

These temporal parameters will be investigated experimentally during the
temporal-experiment phase.