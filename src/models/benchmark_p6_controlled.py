
from pathlib import Path
import argparse
import time

import joblib
import librosa
import numpy as np
import pandas as pd
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
    parser.add_argument("--repeats", type=int, default=4)
    args = parser.parse_args()

    if args.repeats < 2 or args.warmup < 0:
        raise ValueError("Invalid repeats or warmup")

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

    if len(waveform) <= expected_samples:
        raise ValueError("Audio too short")

    device = torch.device("cuda")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME, trust_remote_code=True
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME, trust_remote_code=True
    ).to(device)
    model.eval()

    v_scaler = joblib.load(MODEL_DIR / "layer_4/scaler.joblib")
    v_model = joblib.load(MODEL_DIR / "layer_4/valence_ridge.joblib")
    a_scaler = joblib.load(MODEL_DIR / "layer_8/scaler.joblib")
    a_model = joblib.load(MODEL_DIR / "layer_8/arousal_ridge.joblib")

    end_samples = np.arange(
        expected_samples,
        len(waveform) + 1,
        int(round(HOP_SECONDS * SAMPLE_RATE)),
        dtype=np.int64,
    )

    windows = [
        waveform[end - expected_samples:end]
        for end in end_samples
    ]

    def infer(window, precision):
        if precision == "fp16":
            context = torch.autocast(
                device_type="cuda", dtype=torch.float16
            )
        else:
            context = torch.autocast(
                device_type="cuda", enabled=False
            )

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
                v_scaler.transform(embeddings[4].reshape(1, -1))
            )[0]
        )
        arousal = float(
            a_model.predict(
                a_scaler.transform(embeddings[8].reshape(1, -1))
            )[0]
        )

        if not np.isfinite([valence, arousal]).all():
            raise ValueError("Non-finite prediction")

        return valence, arousal

    # Warm up both modes before collecting measurements.
    for _ in range(args.warmup):
        for precision in ("fp32", "fp16"):
            infer(windows[0], precision)

    synchronize(device)

    rows = []

    for repeat in range(args.repeats):
        # Alternate mode order to reduce systematic order bias.
        order = (
            ("fp32", "fp16")
            if repeat % 2 == 0
            else ("fp16", "fp32")
        )

        for index, window in enumerate(windows):
            for precision in order:
                synchronize(device)
                start = time.perf_counter()

                valence, arousal = infer(window, precision)

                synchronize(device)
                latency_ms = (
                    time.perf_counter() - start
                ) * 1000

                rows.append({
                    "song_id": args.song_id,
                    "repeat": repeat,
                    "index": index,
                    "audio_time_seconds": end_samples[index] / SAMPLE_RATE,
                    "precision": precision,
                    "valence": valence,
                    "arousal": arousal,
                    "latency_ms": latency_ms,
                })

    raw = pd.DataFrame(rows)

    summary = (
        raw.groupby(["repeat", "precision"])["latency_ms"]
        .agg(
            predictions="count",
            mean_latency_ms="mean",
            median_latency_ms="median",
            max_latency_ms="max",
        )
        .reset_index()
    )

    overall = (
        raw.groupby("precision")["latency_ms"]
        .agg(
            predictions="count",
            mean_latency_ms="mean",
            median_latency_ms="median",
            max_latency_ms="max",
        )
        .reset_index()
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prefix = f"EXP_P6_CONTROLLED_song_{args.song_id}"

    raw.to_csv(OUTPUT_DIR / f"{prefix}_raw.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"{prefix}_by_repeat.csv", index=False)
    overall.to_csv(OUTPUT_DIR / f"{prefix}_overall.csv", index=False)

    print("\n===== CONTROLLED P6 BENCHMARK =====")
    print("\nBy repeat:")
    print(summary.to_string(index=False))
    print("\nOverall:")
    print(overall.to_string(index=False))
    print("\nTEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()

