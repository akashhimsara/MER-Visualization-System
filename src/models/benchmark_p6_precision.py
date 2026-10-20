
from pathlib import Path
import argparse
import time
from contextlib import nullcontext

import joblib
import librosa
import numpy as np
import pandas as pd
import psutil
import torch

from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.models.mert_early_exit_safe import extract_mert_early_exit_safe


ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"
SPLIT_FILE = ROOT / "data/splits/deam_song_split_v1.csv"
AUDIO_DIR = ROOT / "data/raw/deam/MEMD_audio"
OUTPUT_DIR = ROOT / "outputs/results"

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5
HOP_SECONDS = 1.0


def synchronize(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--song-id", type=int, default=1637)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument(
        "--precision",
        choices=("fp32", "fp16", "bf16"),
        default="fp32",
    )
    args = parser.parse_args()

    if args.duration <= CONTEXT_SECONDS:
        raise ValueError("Duration must exceed context length")

    if args.warmup < 0:
        raise ValueError("Warmup cannot be negative")

    splits = pd.read_csv(SPLIT_FILE)
    selected = splits.loc[splits["song_id"] == args.song_id]

    if len(selected) != 1 or selected.iloc[0]["split"] != "train":
        raise ValueError("Only TRAIN songs are allowed")

    waveform, _ = librosa.load(
        AUDIO_DIR / f"{args.song_id}.mp3",
        sr=SAMPLE_RATE,
        mono=True,
        duration=args.duration,
    )

    expected_samples = CONTEXT_SECONDS * SAMPLE_RATE

    if len(waveform) < expected_samples:
        raise ValueError("Audio too short")

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    if args.precision != "fp32" and device.type != "cuda":
        raise RuntimeError("Mixed precision benchmark requires CUDA")

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)
    model.eval()

    v_scaler = joblib.load(MODEL_DIR / "layer_4/scaler.joblib")
    v_model = joblib.load(MODEL_DIR / "layer_4/valence_ridge.joblib")
    a_scaler = joblib.load(MODEL_DIR / "layer_8/scaler.joblib")
    a_model = joblib.load(MODEL_DIR / "layer_8/arousal_ridge.joblib")

    process = psutil.Process()

    def infer(window):
        if args.precision == "fp16":
            context = torch.autocast(
                device_type="cuda",
                dtype=torch.float16,
            )
        elif args.precision == "bf16":
            context = torch.autocast(
                device_type="cuda",
                dtype=torch.bfloat16,
            )
        else:
            context = nullcontext()

        with context:
            embeddings = extract_mert_early_exit_safe(
                waveform=window,
                model=model,
                processor=processor,
                device=device,
                sample_rate=SAMPLE_RATE,
                exit_layer=8,
                requested_layers=(4, 8),
            )

        valence = float(
            v_model.predict(
                v_scaler.transform(
                    embeddings[4].reshape(1, -1)
                )
            )[0]
        )

        arousal = float(
            a_model.predict(
                a_scaler.transform(
                    embeddings[8].reshape(1, -1)
                )
            )[0]
        )

        if not np.isfinite([valence, arousal]).all():
            raise ValueError("Non-finite prediction")

        return valence, arousal

    warmup_window = waveform[:expected_samples]

    for _ in range(args.warmup):
        infer(warmup_window)

    synchronize(device)

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    rows = []

    end_samples = np.arange(
        expected_samples,
        len(waveform) + 1,
        int(round(HOP_SECONDS * SAMPLE_RATE)),
        dtype=np.int64,
    )

    for index, end_sample in enumerate(end_samples):
        window = waveform[
            end_sample - expected_samples:end_sample
        ]

        synchronize(device)
        start = time.perf_counter()

        valence, arousal = infer(window)

        synchronize(device)
        latency_ms = (time.perf_counter() - start) * 1000

        rows.append({
            "song_id": args.song_id,
            "precision": args.precision,
            "index": index,
            "audio_time_seconds": end_sample / SAMPLE_RATE,
            "valence": valence,
            "arousal": arousal,
            "latency_ms": latency_ms,
            "rss_memory_mb": process.memory_info().rss / 1024**2,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No benchmark windows generated")

    gpu_peak_allocated_mb = (
        torch.cuda.max_memory_allocated(device) / 1024**2
        if device.type == "cuda" else 0.0
    )

    gpu_peak_reserved_mb = (
        torch.cuda.max_memory_reserved(device) / 1024**2
        if device.type == "cuda" else 0.0
    )

    total_inference_seconds = df["latency_ms"].sum() / 1000

    summary = {
        "song_id": args.song_id,
        "precision": args.precision,
        "context_seconds": CONTEXT_SECONDS,
        "hop_seconds": HOP_SECONDS,
        "predictions": len(df),
        "mean_latency_ms": df["latency_ms"].mean(),
        "p50_latency_ms": df["latency_ms"].quantile(0.50),
        "p95_latency_ms": df["latency_ms"].quantile(0.95),
        "max_latency_ms": df["latency_ms"].max(),
        "throughput_predictions_per_second":
            len(df) / total_inference_seconds,
        "peak_observed_rss_mb": df["rss_memory_mb"].max(),
        "gpu_peak_allocated_mb": gpu_peak_allocated_mb,
        "gpu_peak_reserved_mb": gpu_peak_reserved_mb,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = (
        OUTPUT_DIR /
        f"EXP_P6_PRECISION_{args.precision}_song_{args.song_id}_raw.csv"
    )
    summary_path = (
        OUTPUT_DIR /
        f"EXP_P6_PRECISION_{args.precision}_song_{args.song_id}_summary.csv"
    )

    df.to_csv(raw_path, index=False)
    pd.DataFrame([summary]).to_csv(summary_path, index=False)

    print("\n===== P6 PRECISION BENCHMARK =====")
    print(pd.DataFrame([summary]).to_string(index=False))
    print("\nSaved:", raw_path)
    print("Saved:", summary_path)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()

