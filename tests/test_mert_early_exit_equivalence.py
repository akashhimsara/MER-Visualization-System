
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor


MODEL_NAME = "m-a-p/MERT-v1-95M"


class EarlyExitSignal(Exception):
    pass


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)

    model.eval()

    t = np.arange(120000, dtype=np.float32) / 24000
    waveform = (
        0.1 * np.sin(2 * np.pi * 220 * t)
    ).astype(np.float32)

    inputs = processor(
        waveform,
        sampling_rate=24000,
        return_tensors="pt",
    )

    input_values = inputs["input_values"].to(device)

    with torch.inference_mode():
        full = model(
            input_values,
            output_hidden_states=True,
        )

    full_l4 = full.hidden_states[4].mean(dim=1)
    full_l8 = full.hidden_states[8].mean(dim=1)

    captured = {}

    def capture_layer4(module, args, output):
        captured[4] = output[0].detach()

    def stop_after_layer8(module, args, output):
        captured[8] = output[0].detach()
        raise EarlyExitSignal()

    hook4 = model.encoder.layers[3].register_forward_hook(
        capture_layer4
    )

    hook8 = model.encoder.layers[7].register_forward_hook(
        stop_after_layer8
    )

    try:
        with torch.inference_mode():
            try:
                model(
                    input_values,
                    output_hidden_states=False,
                )
            except EarlyExitSignal:
                pass
    finally:
        hook4.remove()
        hook8.remove()

    assert 4 in captured
    assert 8 in captured

    early_l4 = captured[4].mean(dim=1)
    early_l8 = captured[8].mean(dim=1)

    diff4 = torch.max(
        torch.abs(full_l4 - early_l4)
    ).item()

    diff8 = torch.max(
        torch.abs(full_l8 - early_l8)
    ).item()

    print("===== EARLY EXIT EQUIVALENCE =====")
    print("Layer 4 max difference:", diff4)
    print("Layer 8 max difference:", diff8)

    assert torch.allclose(
        full_l4, early_l4,
        atol=1e-5,
        rtol=1e-5,
    )

    assert torch.allclose(
        full_l8, early_l8,
        atol=1e-5,
        rtol=1e-5,
    )

    print("Full vs early-exit embeddings: PASS")
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
