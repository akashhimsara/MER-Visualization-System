import numpy as np
import torch


@torch.no_grad()
def extract_mert_layer_embeddings(
    waveform,
    model,
    processor,
    device,
    sample_rate=24000,
    layers=(4, 8, 12),
):
    """
    Extract mean-pooled MERT embeddings from selected hidden layers.

    Parameters
    ----------
    waveform : np.ndarray
        Mono audio waveform sampled at 24 kHz.

    model :
        Loaded MERT model.

    processor :
        MERT feature extractor / processor.

    device :
        torch.device used for inference.

    sample_rate : int
        Model-native sample rate.

    layers : tuple
        Hidden-state layers to extract.

    Returns
    -------
    dict
        Mapping:
            layer_number -> 768D float32 embedding
    """

    waveform = np.asarray(waveform, dtype=np.float32)

    if waveform.ndim != 1:
        raise ValueError(
            f"Expected mono 1D waveform, got shape {waveform.shape}"
        )

    inputs = processor(
        waveform,
        sampling_rate=sample_rate,
        return_tensors="pt",
    )

    input_values = inputs["input_values"].to(device)

    outputs = model(
        input_values,
        output_hidden_states=True,
    )

    hidden_states = outputs.hidden_states

    embeddings = {}

    for layer in layers:

        if layer >= len(hidden_states):
            raise ValueError(
                f"Requested layer {layer}, but model returned "
                f"{len(hidden_states)} hidden states."
            )

        hidden = hidden_states[layer]

        # hidden:
        # [batch, time_steps, hidden_size]

        pooled = hidden.mean(dim=1)

        embedding = (
            pooled
            .squeeze(0)
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32)
        )

        embeddings[layer] = embedding

    return embeddings