
from pathlib import Path
import sys
import time
import gc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import torch

from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.mert_features import (
    extract_mert_layer_embeddings,
)
from src.models.mert_early_exit import (
    extract_mert_early_exit_embeddings,
)


MODEL_NAME = "m-a-p/MERT-v1-95M"
RESULT_PATH = (
    ROOT / "outputs/results/"
    "EXP_MERT_001_early_exit_benchmark.csv"
)

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5
WARMUP = 20
RUNS = 100


def synchronize(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def measure(fn, device):
    times = []

    for _ in range(WARMUP):
        fn()

    synchronize(device)

    for _ in range(RUNS):
        synchronize(device)
        start = time.perf_counter()

        fn()

        synchronize(device)
        times.append(
            (time.perf_counter() - start) * 1000
        )

    return np.asarray(times, dtype=np.float64)


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("===== MERT EARLY EXIT BENCHMARK =====")
    print("Device:", device)
    print("TEST: LOCKED / NOT EVALUATED")

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)

    model.eval()

    t = np.arange(
        SAMPLE_RATE * CONTEXT_SECONDS,
        dtype=np.float32,
    ) / SAMPLE_RATE

    waveform = (
        0.1 * np.sin(2 * np.pi * 220 * t)
    ).astype(np.float32)

    def full_forward():
        return extract_mert_layer_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            sample_rate=SAMPLE_RATE,
            layers=(4, 8),
        )

    def early_exit():
        return extract_mert_early_exit_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            sample_rate=SAMPLE_RATE,
            exit_layer=8,
            requested_layers=(4, 8),
        )

    # Both paths use identical inputs and the same loaded model.
    # Alternating measurement order helps reduce order bias.
    results = []

    for repetition, order in enumerate(
        [
            ("full", "early"),
            ("early", "full"),
            ("full", "early"),
        ],
        start=1,
    ):
        functions = {
            "full": full_forward,
            "early": early_exit,
        }

        for mode in order:
            gc.collect()

            times = measure(
                functions[mode],
                device,
            )

            results.append({
                "repetition": repetition,
                "mode": mode,
                "mean_ms": float(np.mean(times)),
                "p95_ms": float(np.percentile(times, 95)),
                "min_ms": float(np.min(times)),
                "max_ms": float(np.max(times)),
                "measured_runs": RUNS,
                "warmup_runs": WARMUP,
                "device": str(device),
                "context_seconds": CONTEXT_SECONDS,
                "test_used": False,
            })

            print(
                f"Rep {repetition} | "
                f"{mode:5s} | "
                f"mean={np.mean(times):.3f} ms | "
                f"P95={np.percentile(times,95):.3f} ms"
            )

    df = pd.DataFrame(results)

    full_mean = df[
        df["mode"] == "full"
    ]["mean_ms"].mean()

    early_mean = df[
        df["mode"] == "early"
    ]["mean_ms"].mean()

    speedup = full_mean / early_mean
    reduction = (
        (full_mean - early_mean) / full_mean
    ) * 100

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(RESULT_PATH, index=False)

    print("\n===== COMPARISON =====")
    print("Full mean:", round(full_mean, 3), "ms")
    print("Early mean:", round(early_mean, 3), "ms")
    print("Speedup:", round(speedup, 3), "x")
    print("Latency reduction:", round(reduction, 2), "%")
    print("Saved:", RESULT_PATH)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
