
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.mert_early_exit import (
    extract_mert_early_exit_embeddings,
)
from src.models.mert_early_exit_safe import (
    extract_mert_early_exit_safe,
)

MODEL_NAME = "m-a-p/MERT-v1-95M"
SAMPLE_RATE = 24000
DURATION = 5
LAYERS = (4, 8)


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("===== SAFE EARLY EXIT EQUIVALENCE =====")
    print("Device:", device)

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device).eval()

    t = np.arange(
        SAMPLE_RATE * DURATION,
        dtype=np.float32,
    ) / SAMPLE_RATE

    rng = np.random.default_rng(42)

    signals = {
        "silence": np.zeros_like(t),
        "220Hz": np.sin(2 * np.pi * 220 * t).astype(np.float32),
        "880Hz": np.sin(2 * np.pi * 880 * t).astype(np.float32),
        "noise": rng.normal(0, 0.1, len(t)).astype(np.float32),
    }

    checks = 0

    for name, waveform in signals.items():
        inputs = processor(
            waveform,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
        )

        with torch.inference_mode():
            outputs = model(
                inputs["input_values"].to(device),
                output_hidden_states=True,
            )

        reference = {
            layer: (
                outputs.hidden_states[layer]
                .mean(dim=1)
                .squeeze(0)
                .cpu()
                .numpy()
            )
            for layer in LAYERS
        }

        old = extract_mert_early_exit_embeddings(
            waveform,
            model,
            processor,
            device,
        )

        safe = extract_mert_early_exit_safe(
            waveform,
            model,
            processor,
            device,
        )

        for layer in LAYERS:
            old_diff = np.max(
                np.abs(reference[layer] - old[layer])
            )

            safe_diff = np.max(
                np.abs(reference[layer] - safe[layer])
            )

            passed = np.allclose(
                reference[layer],
                safe[layer],
                atol=1e-5,
                rtol=1e-5,
            )

            print(
                f"{name:8s} | Layer {layer} | "
                f"old diff={old_diff:.8f} | "
                f"safe diff={safe_diff:.8f} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

            assert passed, (
                f"Safe early exit mismatch: "
                f"{name}, layer {layer}"
            )

            checks += 1

    print("Total checks:", checks)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
