
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
import psutil
import torch

from transformers import AutoModel, Wav2Vec2FeatureExtractor


MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"
RESULT_PATH = (
    ROOT / "outputs/results/EXP_MERT_001_pipeline_benchmark.csv"
)

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5
SAMPLES = SAMPLE_RATE * CONTEXT_SECONDS

WARMUP_RUNS = 20
MEASURED_RUNS = 100


def synchronize(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def summarize(values):
    values = np.asarray(values, dtype=np.float64)
    return {
        "mean_ms": float(np.mean(values)),
        "p95_ms": float(np.percentile(values, 95)),
        "min_ms": float(np.min(values)),
        "max_ms": float(np.max(values)),
    }


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("===== EXP_MERT_001 PIPELINE BENCHMARK =====")
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

    v_scaler = joblib.load(
        MODEL_DIR / "layer_4/scaler.joblib"
    )
    v_model = joblib.load(
        MODEL_DIR / "layer_4/valence_ridge.joblib"
    )

    a_scaler = joblib.load(
        MODEL_DIR / "layer_8/scaler.joblib"
    )
    a_model = joblib.load(
        MODEL_DIR / "layer_8/arousal_ridge.joblib"
    )

    # Deterministic synthetic input.
    # Benchmark only; not a predictive-quality test.
    t = np.arange(SAMPLES, dtype=np.float32) / SAMPLE_RATE
    waveform = (
        0.1 * np.sin(2 * np.pi * 220.0 * t)
    ).astype(np.float32)

    process = psutil.Process()
    cpu_start = process.cpu_times()
    wall_start = time.perf_counter()

    processor_times = []
    mert_times = []
    pooling_times = []
    ridge_times = []
    end_to_end_times = []
    rss_samples_mb = []

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    with torch.inference_mode():
        for run in range(WARMUP_RUNS + MEASURED_RUNS):
            synchronize(device)
            start_total = time.perf_counter()

            # 1. Processor and host-to-device transfer
            start = time.perf_counter()

            inputs = processor(
                waveform,
                sampling_rate=SAMPLE_RATE,
                return_tensors="pt",
            )

            input_values = inputs["input_values"].to(device)

            synchronize(device)
            processor_ms = (
                time.perf_counter() - start
            ) * 1000

            # 2. Full MERT forward pass
            synchronize(device)
            start = time.perf_counter()

            outputs = model(
                input_values,
                output_hidden_states=True,
            )

            synchronize(device)
            mert_ms = (
                time.perf_counter() - start
            ) * 1000

            # 3. Mean pooling + CPU transfer
            start = time.perf_counter()

            layer_4 = (
                outputs.hidden_states[4]
                .mean(dim=1)
                .squeeze(0)
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            layer_8 = (
                outputs.hidden_states[8]
                .mean(dim=1)
                .squeeze(0)
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            synchronize(device)
            pooling_ms = (
                time.perf_counter() - start
            ) * 1000

            # 4. Selected Ridge predictions
            start = time.perf_counter()

            valence = float(
                v_model.predict(
                    v_scaler.transform(
                        layer_4.reshape(1, -1)
                    )
                )[0]
            )

            arousal = float(
                a_model.predict(
                    a_scaler.transform(
                        layer_8.reshape(1, -1)
                    )
                )[0]
            )

            ridge_ms = (
                time.perf_counter() - start
            ) * 1000

            synchronize(device)
            total_ms = (
                time.perf_counter() - start_total
            ) * 1000

            assert np.isfinite(valence)
            assert np.isfinite(arousal)

            if run >= WARMUP_RUNS:
                processor_times.append(processor_ms)
                mert_times.append(mert_ms)
                pooling_times.append(pooling_ms)
                ridge_times.append(ridge_ms)
                end_to_end_times.append(total_ms)

                rss_samples_mb.append(
                    process.memory_info().rss / (1024 ** 2)
                )

    wall_elapsed = time.perf_counter() - wall_start
    cpu_end = process.cpu_times()

    cpu_seconds = (
        cpu_end.user + cpu_end.system
        - cpu_start.user - cpu_start.system
    )

    avg_process_cpu_percent = (
        100 * cpu_seconds / wall_elapsed
    )

    summaries = {
        "processor": summarize(processor_times),
        "mert": summarize(mert_times),
        "pooling": summarize(pooling_times),
        "ridge": summarize(ridge_times),
        "end_to_end": summarize(end_to_end_times),
    }

    rows = []

    for stage, metrics in summaries.items():
        rows.append({
            "experiment_id": "EXP_MERT_001",
            "stage": stage,
            "device": str(device),
            "context_seconds": CONTEXT_SECONDS,
            "warmup_runs": WARMUP_RUNS,
            "measured_runs": MEASURED_RUNS,
            "mean_ms": metrics["mean_ms"],
            "p95_ms": metrics["p95_ms"],
            "min_ms": metrics["min_ms"],
            "max_ms": metrics["max_ms"],
            "avg_process_cpu_percent":
                avg_process_cpu_percent,
            "peak_process_rss_mb":
                max(rss_samples_mb),
            "peak_gpu_allocated_mb": (
                torch.cuda.max_memory_allocated(device)
                / (1024 ** 2)
                if device.type == "cuda" else 0.0
            ),
            "test_used": False,
        })

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(rows).to_csv(
        RESULT_PATH,
        index=False,
    )

    print("\n===== BENCHMARK SUMMARY =====")

    for stage, metrics in summaries.items():
        print(
            f"{stage:12s} | "
            f"mean={metrics['mean_ms']:.3f} ms | "
            f"P95={metrics['p95_ms']:.3f} ms"
        )

    print(
        "Average process CPU:",
        round(avg_process_cpu_percent, 2),
        "%",
    )

    print(
        "Peak process RAM:",
        round(max(rss_samples_mb), 2),
        "MB",
    )

    if device.type == "cuda":
        print(
            "Peak GPU allocated:",
            round(
                torch.cuda.max_memory_allocated(device)
                / (1024 ** 2),
                2,
            ),
            "MB",
        )

    print("Results saved:", RESULT_PATH)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
