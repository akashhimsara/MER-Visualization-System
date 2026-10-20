
from pathlib import Path
import argparse
from contextlib import nullcontext

import joblib
import librosa
import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.models.mert_early_exit_safe import extract_mert_early_exit_safe


ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"
SPLIT_FILE = ROOT / "data/splits/deam_song_split_v1.csv"
TARGET_FILE = ROOT / "data/processed/deam_paired_va_targets_v1.csv"
AUDIO_DIR = ROOT / "data/raw/deam/MEMD_audio"
OUTPUT_DIR = ROOT / "outputs/results"

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5
HOP_MS = 1000
PRECISIONS = ("fp32", "fp16", "bf16")


def ccc(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    my, mp = y.mean(), p.mean()
    vy, vp = y.var(), p.var()
    cov = np.mean((y - my) * (p - mp))

    denom = vy + vp + (my - mp) ** 2
    return float(2 * cov / denom) if denom > 0 else np.nan


def metrics(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    pearson = (
        float(np.corrcoef(y, p)[0, 1])
        if len(y) > 1 and y.std() > 0 and p.std() > 0
        else np.nan
    )

    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(np.sqrt(mean_squared_error(y, p))),
        "pearson": pearson,
        "ccc": ccc(y, p),
        "r2": float(r2_score(y, p)) if len(y) > 1 else np.nan,
    }


def precision_context(precision):
    if precision == "fp16":
        return torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
        )
    if precision == "bf16":
        return torch.autocast(
            device_type="cuda",
            dtype=torch.bfloat16,
        )
    return nullcontext()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-songs", type=int, default=3)
    args = parser.parse_args()

    if not 1 <= args.max_songs <= 270:
        raise ValueError("--max-songs must be between 1 and 270")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for precision comparison")

    device = torch.device("cuda")

    splits = pd.read_csv(SPLIT_FILE)
    targets = pd.read_csv(TARGET_FILE)

    validation_ids = sorted(
        splits.loc[
            splits["split"] == "validation", "song_id"
        ].astype(int).tolist()
    )

    assert len(validation_ids) == 270
    selected_ids = validation_ids[:args.max_songs]

    selected_targets = targets.loc[
        (targets["split"] == "validation")
        & (targets["song_id"].isin(selected_ids))
        & ((targets["timestamp_ms"] - 15000) % HOP_MS == 0)
    ].copy()

    if selected_targets.empty:
        raise ValueError("No validation targets selected")

    if selected_targets.duplicated(
        ["song_id", "timestamp_ms"]
    ).any():
        raise ValueError("Duplicate canonical timestamps")

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

    rows = []
    window_samples = CONTEXT_SECONDS * SAMPLE_RATE

    for song_index, song_id in enumerate(selected_ids, start=1):
        song_targets = selected_targets.loc[
            selected_targets["song_id"] == song_id
        ].sort_values("timestamp_ms")

        if song_targets.empty:
            raise ValueError(f"No targets for song {song_id}")

        audio_path = AUDIO_DIR / f"{song_id}.mp3"

        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)

        waveform, _ = librosa.load(
            audio_path,
            sr=SAMPLE_RATE,
            mono=True,
        )

        print(
            f"Processing validation song "
            f"{song_index}/{len(selected_ids)}: {song_id}",
            flush=True,
        )

        for target in song_targets.itertuples(index=False):
            timestamp_ms = int(target.timestamp_ms)
            end_sample = int(
                round(timestamp_ms * SAMPLE_RATE / 1000)
            )
            start_sample = end_sample - window_samples

            if start_sample < 0 or end_sample > len(waveform):
                raise ValueError(
                    f"Audio/target mismatch: "
                    f"song={song_id}, time={timestamp_ms}"
                )

            window = waveform[start_sample:end_sample]

            if len(window) != window_samples:
                raise ValueError("Invalid window length")

            for precision in PRECISIONS:
                with precision_context(precision):
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
                    raise ValueError(
                        f"Non-finite prediction: "
                        f"{song_id}, {precision}, {timestamp_ms}"
                    )

                rows.append({
                    "song_id": int(song_id),
                    "timestamp_ms": timestamp_ms,
                    "precision": precision,
                    "true_valence": float(target.valence),
                    "true_arousal": float(target.arousal),
                    "pred_valence": valence,
                    "pred_arousal": arousal,
                })

    predictions = pd.DataFrame(rows)

    expected = len(selected_targets) * len(PRECISIONS)

    if len(predictions) != expected:
        raise ValueError("Prediction count mismatch")

    if predictions.duplicated(
        ["song_id", "timestamp_ms", "precision"]
    ).any():
        raise ValueError("Duplicate prediction keys")

    summary = []

    for precision in PRECISIONS:
        subset = predictions.loc[
            predictions["precision"] == precision
        ]

        if len(subset) != len(selected_targets):
            raise ValueError("Precision timestamp coverage mismatch")

        for target in ("valence", "arousal"):
            result = metrics(
                subset[f"true_{target}"],
                subset[f"pred_{target}"],
            )

            summary.append({
                "precision": precision,
                "target": target,
                "songs": len(selected_ids),
                "n": len(subset),
                **result,
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = (
        OUTPUT_DIR /
        f"EXP_P6_PRECISION_validation_{len(selected_ids)}songs_raw.csv"
    )
    summary_path = (
        OUTPUT_DIR /
        f"EXP_P6_PRECISION_validation_{len(selected_ids)}songs_summary.csv"
    )

    predictions.to_csv(raw_path, index=False)
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(summary_path, index=False)

    print("\n===== P6 PRECISION VALIDATION =====")
    print(summary_df.to_string(index=False))
    print("\nSaved:", raw_path)
    print("Saved:", summary_path)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
