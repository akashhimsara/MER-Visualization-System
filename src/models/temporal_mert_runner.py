
from pathlib import Path
import argparse
import csv
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
CONTEXT_SECONDS = 5.0
HOPS = (0.5, 1.0, 2.0)


def find_audio(song_id):
    matches = list(AUDIO_DIR.rglob(f"{song_id}.mp3"))

    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one audio file for {song_id}; found {len(matches)}"
        )

    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--song-id", required=True)
    parser.add_argument("--max-seconds", type=float, default=30.0)
    args = parser.parse_args()

    splits = pd.read_csv(SPLIT_FILE)
    splits["song_id"] = splits["song_id"].astype(str)

    selected = splits.loc[
        splits["song_id"] == str(args.song_id)
    ]

    if len(selected) != 1:
        raise ValueError("Song missing or duplicated in split manifest")

    split = selected.iloc[0]["split"]

    if split != "train":
        raise ValueError(
            f"Temporal pilot allows TRAIN only; got {split}"
        )

    audio_path = find_audio(args.song_id)

    waveform, _ = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
        duration=args.max_seconds,
    )

    if len(waveform) < int(CONTEXT_SECONDS * SAMPLE_RATE):
        raise ValueError("Audio shorter than context window")

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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for hop in HOPS:
        end_times = np.arange(
            CONTEXT_SECONDS,
            len(waveform) / SAMPLE_RATE + 1e-8,
            hop,
        )

        for end_time in end_times:
            end_sample = round(end_time * SAMPLE_RATE)
            start_sample = end_sample - round(
                CONTEXT_SECONDS * SAMPLE_RATE
            )

            window = waveform[start_sample:end_sample]

            if len(window) != int(CONTEXT_SECONDS * SAMPLE_RATE):
                continue

            if device.type == "cuda":
                torch.cuda.synchronize()

            start = time.perf_counter()

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

            if device.type == "cuda":
                torch.cuda.synchronize()

            latency_ms = (
                time.perf_counter() - start
            ) * 1000.0

            if not np.isfinite([valence, arousal]).all():
                raise ValueError("Non-finite prediction")

            results.append({
                "song_id": str(args.song_id),
                "split": split,
                "context_seconds": CONTEXT_SECONDS,
                "hop_seconds": hop,
                "audio_time_seconds": round(float(end_time), 3),
                "valence": valence,
                "arousal": arousal,
                "latency_ms": latency_ms,
            })

        print(
            f"Hop {hop}s: "
            f"{sum(r['hop_seconds'] == hop for r in results)} predictions"
        )

    output_path = OUTPUT_DIR / (
        f"EXP_TEMPORAL_001_song_{args.song_id}.csv"
    )

    pd.DataFrame(results).to_csv(output_path, index=False)

    print("Saved:", output_path)
    print("Rows:", len(results))
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
