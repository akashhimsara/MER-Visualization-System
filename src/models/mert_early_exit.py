
import torch
from transformers.modeling_outputs import BaseModelOutput


@torch.no_grad()
def extract_mert_early_exit_embeddings(
    waveform,
    model,
    processor,
    device,
    sample_rate=24000,
    exit_layer=8,
    requested_layers=(4, 8),
):
    """
    Extract MERT embeddings using an early encoder exit.

    The model's original feature extraction and projection
    are preserved. Only the encoder forward is temporarily
    replaced for this inference call.

    Intended for controlled research experiments.
    """

    import numpy as np

    waveform = np.asarray(waveform, dtype=np.float32)

    if waveform.ndim != 1:
        raise ValueError("Expected mono 1D waveform")

    if model.training:
        raise ValueError("Model must be in eval mode")

    if exit_layer < max(requested_layers):
        raise ValueError(
            "Exit layer must cover all requested layers"
        )

    if exit_layer > len(model.encoder.layers):
        raise ValueError("Exit layer exceeds encoder depth")

    inputs = processor(
        waveform,
        sampling_rate=sample_rate,
        return_tensors="pt",
    )

    input_values = inputs["input_values"].to(device)

    encoder = model.encoder
    original_forward = encoder.forward

    def early_forward(
        hidden_states,
        attention_mask=None,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=True,
    ):
        if attention_mask is not None:
            mask = attention_mask.unsqueeze(-1).expand_as(
                hidden_states
            )
            hidden_states = hidden_states.masked_fill(
                ~mask.bool(), 0
            )

            if encoder._use_flash_attention_2:
                attention_mask = (
                    attention_mask
                    if 0 in attention_mask
                    else None
                )
            else:
                attention_mask = (
                    1.0
                    - attention_mask[
                        :, None, None, :
                    ].to(dtype=hidden_states.dtype)
                )

                attention_mask = (
                    attention_mask
                    * torch.finfo(
                        hidden_states.dtype
                    ).min
                )

                attention_mask = attention_mask.expand(
                    attention_mask.shape[0],
                    1,
                    attention_mask.shape[-1],
                    attention_mask.shape[-1],
                )

        position_embeddings = encoder.pos_conv_embed(
            hidden_states
        )

        hidden_states = hidden_states + position_embeddings
        hidden_states = encoder.layer_norm(hidden_states)
        hidden_states = encoder.dropout(hidden_states)

        all_hidden_states = (
            () if output_hidden_states else None
        )

        for i, layer in enumerate(
            encoder.layers[:exit_layer]
        ):
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            layer_outputs = layer(
                hidden_states,
                attention_mask=attention_mask,
                output_attentions=False,
            )

            hidden_states = layer_outputs[0]

        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        return BaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
        )

    try:
        encoder.forward = early_forward

        outputs = model(
            input_values,
            output_hidden_states=True,
        )

    finally:
        encoder.forward = original_forward

    embeddings = {}

    for layer in requested_layers:
        pooled = outputs.hidden_states[layer].mean(dim=1)

        embeddings[layer] = (
            pooled.squeeze(0)
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32)
        )

    return embeddings
