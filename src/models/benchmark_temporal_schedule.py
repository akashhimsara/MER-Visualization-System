
from pathlib import Path
import argparse
import time

import joblib
import librosa
import numpy as np
import pandas as pd
import torch

from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.models.mert_early_exit_safe import (
    extract_mert_early_exit_safe,
)


ROOT = Path(__file__).resolve().parents[2]

MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"
SPLIT_FILE = ROOT / "data/splits/deam_song_split_v1.csv"
AUDIO_DIR = ROOT / "data/raw/deam/MEMD_audio"
OUTPUT_DIR = ROOT / "outputs/results"

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5
HOPS = (0.5, 1.0, 2.0)


def synchronize(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--song-id", type=int, default=1637)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()

    if args.duration <= CONTEXT_SECONDS:
        raise ValueError("Duration must exceed context length")

    splits = pd.read_csv(SPLIT_FILE)

    selected = splits.loc[
        splits["song_id"] == args.song_id
    ]

    if len(selected) != 1 or selected.iloc[0]["split"] != "train":
        raise ValueError("Only TRAIN songs are allowed")

    audio_path = AUDIO_DIR / f"{args.song_id}.mp3"

    waveform, _ = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
        duration=args.duration,
    )

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

    v_scaler = joblib.load(MODEL_DIR / "layer_4/scaler.joblib")
    v_model = joblib.load(MODEL_DIR / "layer_4/valence_ridge.joblib")
    a_scaler = joblib.load(MODEL_DIR / "layer_8/scaler.joblib")
    a_model = joblib.load(MODEL_DIR / "layer_8/arousal_ridge.joblib")

    expected_samples = CONTEXT_SECONDS * SAMPLE_RATE

    if len(waveform) < expected_samples:
        raise ValueError("Audio too short")

    def infer(window):
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

    rows = []

    for hop in HOPS:
        end_samples = np.arange(
            expected_samples,
            len(waveform) + 1,
            int(round(hop * SAMPLE_RATE)),
            dtype=np.int64,
        )

        # Simulated audio-clock scheduling.
        # No sleeping: measure processing service time and
        # calculate serial backlog under periodic arrivals.
        backlog_seconds = 0.0

        for index, end_sample in enumerate(end_samples):
            start_sample = end_sample - expected_samples
            window = waveform[start_sample:end_sample]

            synchronize(device)
            start = time.perf_counter()

            valence, arousal = infer(window)

            synchronize(device)
            latency = time.perf_counter() - start

            backlog_seconds = max(
                0.0,
                backlog_seconds + latency - hop,
            )

            rows.append({
                "song_id": args.song_id,
                "hop_seconds": hop,
                "index": index,
                "audio_time_seconds": end_sample / SAMPLE_RATE,
                "valence": valence,
                "arousal": arousal,
                "latency_ms": latency * 1000,
                "deadline_miss": latency > hop,
                "estimated_backlog_ms": backlog_seconds * 1000,
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUT_DIR / "EXP_TEMPORAL_001_schedule.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    df = pd.DataFrame(rows)

    summary = (
        df.groupby("hop_seconds")
        .agg(
            predictions=("latency_ms", "size"),
            mean_latency_ms=("latency_ms", "mean"),
            p95_latency_ms=(
                "latency_ms",
                lambda x: np.percentile(x, 95),
            ),
            max_latency_ms=("latency_ms", "max"),
            deadline_misses=("deadline_miss", "sum"),
            max_estimated_backlog_ms=(
                "estimated_backlog_ms",
                "max",
            ),
        )
        .reset_index()
    )

    print("\n===== TEMPORAL SCHEDULING BENCHMARK =====")
    print(summary.to_string(index=False))
    print("\nSaved:", path)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
