
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.mert_early_exit_safe import (
    extract_mert_early_exit_safe,
)

MODEL_NAME = "m-a-p/MERT-v1-95M"
SR = 24000
LAYERS = (4, 8)


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    torch.set_num_threads(4)

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device).eval()

    t = np.arange(SR * 5, dtype=np.float32) / SR

    waveforms = [
        np.sin(2 * np.pi * 220 * t).astype(np.float32),
        np.sin(2 * np.pi * 880 * t).astype(np.float32),
    ]

    # Sequential reference
    expected = [
        extract_mert_early_exit_safe(
            waveform, model, processor, device
        )
        for waveform in waveforms
    ]

    # Concurrent inference on the same model instance
    with ThreadPoolExecutor(max_workers=2) as pool:
        actual = list(
            pool.map(
                lambda waveform: extract_mert_early_exit_safe(
                    waveform, model, processor, device
                ),
                waveforms,
            )
        )

    checks = 0

    for i in range(len(waveforms)):
        for layer in LAYERS:
            diff = np.max(
                np.abs(
                    expected[i][layer]
                    - actual[i][layer]
                )
            )

            passed = np.allclose(
                expected[i][layer],
                actual[i][layer],
                atol=1e-5,
                rtol=1e-5,
            )

            print(
                f"Request {i + 1} | Layer {layer} | "
                f"max diff={diff:.8f} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

            assert passed
            checks += 1

    print("Concurrent requests: 2")
    print("Total checks:", checks)
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
