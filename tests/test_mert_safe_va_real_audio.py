
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import librosa
import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.mert_features import (
    extract_mert_layer_embeddings,
)
from src.models.mert_early_exit_safe import (
    extract_mert_early_exit_safe,
)


MODEL_NAME = "m-a-p/MERT-v1-95M"

TARGET_FILE = (
    ROOT / "data/processed/deam_paired_va_targets_v1.csv"
)
AUDIO_DIR = ROOT / "data/raw/deam/MEMD_audio"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"

SR = 24000
CONTEXT_SECONDS = 5
EXPECTED_SAMPLES = SR * CONTEXT_SECONDS
LAYERS = (4, 8)


def load_predictors():
    predictors = {}

    for target, layer in (
        ("valence", 4),
        ("arousal", 8),
    ):
        folder = MODEL_DIR / f"layer_{layer}"

        predictors[target] = {
            "layer": layer,
            "scaler": joblib.load(
                folder / "scaler.joblib"
            ),
            "ridge": joblib.load(
                folder / f"{target}_ridge.joblib"
            ),
        }

    return predictors


def predict_va(embeddings, predictors):
    predictions = {}

    for target, components in predictors.items():
        layer = components["layer"]

        X = np.asarray(
            embeddings[layer],
            dtype=np.float32,
        ).reshape(1, -1)

        X_scaled = components["scaler"].transform(X)

        predictions[target] = float(
            components["ridge"].predict(X_scaled)[0]
        )

    return predictions


def select_real_audio_samples():
    targets = pd.read_csv(TARGET_FILE)

    required_columns = {
        "song_id",
        "split",
        "timestamp_ms",
        "timestamp_sec",
    }

    assert required_columns.issubset(targets.columns)

    # TEST partition must remain locked.
    allowed = targets[
        targets["split"].isin(["train", "validation"])
    ].copy()

    assert len(allowed) > 0
    assert not (allowed["split"] == "test").any()

    selected = []

    for split in ("train", "validation"):
        subset = allowed[
            allowed["split"] == split
        ]

        song_ids = sorted(
            subset["song_id"].unique()
        )[:5]

        assert len(song_ids) == 5

        for song_id in song_ids:
            song_rows = subset[
                subset["song_id"] == song_id
            ].sort_values("timestamp_ms")

            # Use the middle timestamp for each song.
            row = song_rows.iloc[
                len(song_rows) // 2
            ]

            selected.append(row)

    assert len(selected) == 10

    return selected


def load_audio_window(song_id, timestamp_sec):
    audio_path = AUDIO_DIR / f"{song_id}.mp3"

    waveform_full, sr = librosa.load(
        audio_path,
        sr=SR,
        mono=True,
    )

    assert sr == SR
    assert np.isfinite(waveform_full).all()

    start_sample = int(
        round(
            (timestamp_sec - CONTEXT_SECONDS) * SR
        )
    )

    end_sample = (
        start_sample + EXPECTED_SAMPLES
    )

    assert start_sample >= 0

    waveform = waveform_full[
        start_sample:end_sample
    ]

    if len(waveform) < EXPECTED_SAMPLES:
        waveform = np.pad(
            waveform,
            (
                0,
                EXPECTED_SAMPLES - len(waveform),
            ),
            mode="constant",
        )

    elif len(waveform) > EXPECTED_SAMPLES:
        waveform = waveform[:EXPECTED_SAMPLES]

    assert waveform.shape == (
        EXPECTED_SAMPLES,
    )

    return waveform


def main():
    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "===== REAL DEAM SAFE MERT VA "
        "PREDICTION EQUIVALENCE ====="
    )
    print("Device:", device)

    selected = select_real_audio_samples()

    processor = (
        Wav2Vec2FeatureExtractor.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
        )
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)

    model.eval()

    predictors = load_predictors()

    checks = 0
    max_difference = 0.0

    for row in selected:
        song_id = int(row["song_id"])
        split = str(row["split"])
        timestamp_sec = float(
            row["timestamp_sec"]
        )

        assert split in ("train", "validation")

        waveform = load_audio_window(
            song_id,
            timestamp_sec,
        )

        # Original full 12-layer MERT.
        full_embeddings = (
            extract_mert_layer_embeddings(
                waveform=waveform,
                model=model,
                processor=processor,
                device=device,
                sample_rate=SR,
                layers=LAYERS,
            )
        )

        # Safe 8-layer early-exit MERT.
        safe_embeddings = (
            extract_mert_early_exit_safe(
                waveform=waveform,
                model=model,
                processor=processor,
                device=device,
                sample_rate=SR,
                exit_layer=8,
                requested_layers=LAYERS,
            )
        )

        for layer in LAYERS:
            assert full_embeddings[layer].shape == (
                768,
            )
            assert safe_embeddings[layer].shape == (
                768,
            )

        # Use exactly the same saved scalers
        # and Ridge models for both paths.
        full_predictions = predict_va(
            full_embeddings,
            predictors,
        )

        safe_predictions = predict_va(
            safe_embeddings,
            predictors,
        )

        for target in ("valence", "arousal"):
            full_value = full_predictions[
                target
            ]
            safe_value = safe_predictions[
                target
            ]

            difference = abs(
                full_value - safe_value
            )

            max_difference = max(
                max_difference,
                difference,
            )

            passed = np.isclose(
                full_value,
                safe_value,
                atol=1e-6,
                rtol=0,
            )

            print(
                f"{split:10s} | "
                f"Song {song_id:4d} | "
                f"{target:7s} | "
                f"full={full_value:.6f} | "
                f"safe={safe_value:.6f} | "
                f"diff={difference:.8f} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

            assert passed, (
                f"Prediction mismatch: "
                f"song={song_id}, "
                f"split={split}, "
                f"target={target}, "
                f"diff={difference}"
            )

            checks += 1

    assert checks == 20

    print("\n===== SUMMARY =====")
    print("Total songs:", len(selected))
    print("Total prediction checks:", checks)
    print(
        "Maximum prediction difference:",
        f"{max_difference:.10f}",
    )
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()

