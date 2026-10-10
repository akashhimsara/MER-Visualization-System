
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.mert_features import (
    extract_mert_layer_embeddings,
)
from src.models.mert_early_exit import (
    extract_mert_early_exit_embeddings,
)


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("===== MULTIPLE-INPUT EARLY EXIT EQUIVALENCE =====")
    print("Device:", device)

    model_name = "m-a-p/MERT-v1-95M"

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        model_name,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
    ).to(device)

    model.eval()

    sr = 24000
    n = sr * 5
    t = np.arange(n, dtype=np.float32) / sr

    rng = np.random.default_rng(42)

    signals = {
        "silence": np.zeros(n, dtype=np.float32),
        "sine_220hz": (
            0.1 * np.sin(2 * np.pi * 220 * t)
        ).astype(np.float32),
        "sine_880hz": (
            0.1 * np.sin(2 * np.pi * 880 * t)
        ).astype(np.float32),
        "white_noise": (
            0.05 * rng.standard_normal(n)
        ).astype(np.float32),
        "mixed_signal": (
            0.1 * np.sin(2 * np.pi * 110 * t)
            + 0.05 * np.sin(2 * np.pi * 440 * t)
        ).astype(np.float32),
    }

    for name, waveform in signals.items():
        full = extract_mert_layer_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            layers=(4, 8),
        )

        early = extract_mert_early_exit_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            exit_layer=8,
            requested_layers=(4, 8),
        )

        for layer in (4, 8):
            assert full[layer].shape == (768,)
            assert early[layer].shape == (768,)

            diff = np.max(
                np.abs(full[layer] - early[layer])
            )

            assert np.allclose(
                full[layer],
                early[layer],
                atol=1e-5,
                rtol=1e-5,
            ), (
                f"{name}, layer {layer}, "
                f"max difference {diff}"
            )

            print(
                f"{name:15s} | "
                f"Layer {layer} | "
                f"max diff={diff:.8f} | PASS"
            )

    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
