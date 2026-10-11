
import numpy as np
import torch


@torch.inference_mode()
def extract_mert_early_exit_safe(
    waveform,
    model,
    processor,
    device,
    sample_rate=24000,
    exit_layer=8,
    requested_layers=(4, 8),
):
    """
    Early-exit MERT inference without monkey-patching.

    Assumptions:
    - MERT-v1-95M architecture inspected in T3.
    - Model is in eval mode.
    - Input is one mono audio window.
    - No attention mask for this fixed-length input.
    """

    if model.training:
        raise ValueError("Model must be in eval mode")

    if model.config.feature_extractor_cqt:
        raise NotImplementedError(
            "CQT-enabled models require an additional "
            "feature extraction path."
        )

    requested_layers = tuple(requested_layers)

    if (
        not requested_layers
        or min(requested_layers) < 1
        or exit_layer < max(requested_layers)
        or exit_layer > len(model.encoder.layers)
    ):
        raise ValueError("Invalid layer configuration")

    waveform = np.asarray(
        waveform,
        dtype=np.float32,
    )

    if waveform.ndim != 1:
        raise ValueError("Expected mono 1D waveform")

    if not np.isfinite(waveform).all():
        raise ValueError("Waveform contains non-finite values")

    inputs = processor(
        waveform,
        sampling_rate=sample_rate,
        return_tensors="pt",
    )

    input_values = inputs["input_values"].to(device)

    # Preserve original MERT feature extraction.
    features = model.feature_extractor(input_values)
    features = features.transpose(1, 2)

    # Preserve original feature projection.
    hidden_states = model.feature_projection(features)

    # Preserve original masking operation.
    hidden_states = model._mask_hidden_states(
        hidden_states,
        mask_time_indices=None,
    )

    encoder = model.encoder

    # Preserve original positional encoding and normalization.
    hidden_states = (
        hidden_states
        + encoder.pos_conv_embed(hidden_states)
    )

    hidden_states = encoder.layer_norm(hidden_states)
    hidden_states = encoder.dropout(hidden_states)

    embeddings = {}

    for layer_number, layer in enumerate(
        encoder.layers[:exit_layer],
        start=1,
    ):
        outputs = layer(
            hidden_states,
            attention_mask=None,
            output_attentions=False,
        )

        hidden_states = outputs[0]

        if layer_number in requested_layers:
            pooled = hidden_states.mean(dim=1)

            embeddings[layer_number] = (
                pooled.squeeze(0)
                .detach()
                .cpu()
                .numpy()
                .astype(np.float32)
            )

    return embeddings
