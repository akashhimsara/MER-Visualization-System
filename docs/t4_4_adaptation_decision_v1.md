# T4.4 — MERT Adaptation Decision

## Objective

Determine whether fine-tuning or adapting the pretrained MERT model is justified by the available validation results, computational resources, and real-time inference requirements.

## Current Evidence

The frozen MERT-only approach achieved validation MAE values of 0.183636 for valence and 0.136370 for arousal.

The hybrid approach improved these results to 0.181762 for valence and 0.135393 for arousal.

In the controlled prepared-window benchmark, frozen MERT-only inference achieved a mean latency of 32.308 ms, compared with 69.259 ms for the hybrid approach.

## Adaptation Considerations

Fine-tuning MERT would require additional GPU training time, hyperparameter selection, validation experiments, and careful controls against overfitting.

The available hardware is an NVIDIA RTX 3050 Laptop GPU with 6 GB VRAM.

The current experiments do not establish that fine-tuning would deliver a sufficiently large improvement to justify its additional computational and experimental cost.

## Decision

**Skip MERT fine-tuning in the current research iteration.**

Retain frozen MERT with safe early-exit inference as the provisional latency-oriented candidate.

Retain the hybrid Ridge model as an accuracy-oriented comparison candidate.

This is a resource-aware scope decision, not evidence that fine-tuning cannot improve performance.

## Revisit Conditions

Reconsider adaptation if later temporal experiments demonstrate inadequate predictive performance, or if additional computational resources and sufficient experimental time become available.

Any future adaptation experiment must use TRAIN data for fitting and VALIDATION data for selection. The held-out TEST partition must remain locked until final evaluation.

## Exit Evidence

T4.4 adaptation decision: **SKIP — justified by current evidence and resource constraints.**

No pretrained MERT weights were modified.