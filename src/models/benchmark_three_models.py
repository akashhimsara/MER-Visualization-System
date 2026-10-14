
from pathlib import Path
import sys
import time
import gc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import joblib
import librosa
import numpy as np
import pandas as pd
import psutil
import torch

from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.traditional_waveform_features import (
    extract_traditional_waveform_features,
)
from src.models.mert_early_exit_safe import (
    extract_mert_early_exit_safe,
)


MODEL_NAME = "m-a-p/MERT-v1-95M"
AUDIO_PATH = ROOT / "data/raw/deam/MEMD_audio/2.mp3"

TRAD_DIR = ROOT / "outputs/models/EXP_TRAD_001"
MERT_DIR = ROOT / "outputs/models/EXP_MERT_001"
HYBRID_DIR = ROOT / "outputs/models/EXP_HYBRID_001"

RESULT_PATH = (
    ROOT / "outputs/results/"
    "EXP_HYBRID_001_controlled_comparison.csv"
)

TRAD_SR = 22050
MERT_SR = 24000
CONTEXT_SECONDS = 5.0
TARGET_TIME = 20.0

WARMUP = 10
RUNS = 50

ORDERS = [
    ("traditional", "mert", "hybrid"),
    ("hybrid", "traditional", "mert"),
    ("mert", "hybrid", "traditional"),
]


def sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def load_window(sr):
    waveform, actual_sr = librosa.load(
        AUDIO_PATH,
        sr=sr,
        mono=True,
        offset=TARGET_TIME - CONTEXT_SECONDS,
        duration=CONTEXT_SECONDS,
    )

    expected = int(round(CONTEXT_SECONDS * sr))

    if abs(len(waveform) - expected) > 1:
        raise ValueError("Unexpected audio length")

    waveform = waveform[:expected]

    if len(waveform) < expected:
        waveform = np.pad(
            waveform,
            (0, expected - len(waveform)),
        )

    assert actual_sr == sr
    assert np.isfinite(waveform).all()

    return waveform.astype(np.float32)


def main():
    assert AUDIO_PATH.exists()

    torch.set_num_threads(4)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    process = psutil.Process()

    traditional_waveform = load_window(TRAD_SR)
    mert_waveform = load_window(MERT_SR)

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    mert_model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)
    mert_model.eval()

    # Traditional saved artifacts
    trad_scaler = joblib.load(
        TRAD_DIR / "scaler.joblib"
    )
    trad_v = joblib.load(
        TRAD_DIR / "valence_ridge.joblib"
    )
    trad_a = joblib.load(
        TRAD_DIR / "arousal_ridge.joblib"
    )

    # MERT saved artifacts
    mert_v_scaler = joblib.load(
        MERT_DIR / "layer_4/scaler.joblib"
    )
    mert_v = joblib.load(
        MERT_DIR / "layer_4/valence_ridge.joblib"
    )

    mert_a_scaler = joblib.load(
        MERT_DIR / "layer_8/scaler.joblib"
    )
    mert_a = joblib.load(
        MERT_DIR / "layer_8/arousal_ridge.joblib"
    )

    # Hybrid saved artifacts
    hybrid_v_scaler = joblib.load(
        HYBRID_DIR / "layer_4/scaler.joblib"
    )
    hybrid_v = joblib.load(
        HYBRID_DIR / "layer_4/valence_ridge.joblib"
    )

    hybrid_a_scaler = joblib.load(
        HYBRID_DIR / "layer_8/scaler.joblib"
    )
    hybrid_a = joblib.load(
        HYBRID_DIR / "layer_8/arousal_ridge.joblib"
    )

    assert trad_scaler.n_features_in_ == 86
    assert mert_v_scaler.n_features_in_ == 768
    assert mert_a_scaler.n_features_in_ == 768
    assert hybrid_v_scaler.n_features_in_ == 854
    assert hybrid_a_scaler.n_features_in_ == 854

    def extract_traditional():
        return extract_traditional_waveform_features(
            traditional_waveform,
            TRAD_SR,
        )

    def extract_mert():
        return extract_mert_early_exit_safe(
            waveform=mert_waveform,
            model=mert_model,
            processor=processor,
            device=device,
            sample_rate=MERT_SR,
            exit_layer=8,
            requested_layers=(4, 8),
        )

    def predict_traditional():
        features = extract_traditional().reshape(1, -1)
        scaled = trad_scaler.transform(features)

        return (
            float(trad_v.predict(scaled)[0]),
            float(trad_a.predict(scaled)[0]),
        )

    def predict_mert():
        embeddings = extract_mert()

        xv = embeddings[4].reshape(1, -1)
        xa = embeddings[8].reshape(1, -1)

        return (
            float(
                mert_v.predict(
                    mert_v_scaler.transform(xv)
                )[0]
            ),
            float(
                mert_a.predict(
                    mert_a_scaler.transform(xa)
                )[0]
            ),
        )

    def predict_hybrid():
        traditional = extract_traditional()
        embeddings = extract_mert()

        xv = np.concatenate([
            traditional,
            embeddings[4],
        ]).reshape(1, -1)

        xa = np.concatenate([
            traditional,
            embeddings[8],
        ]).reshape(1, -1)

        return (
            float(
                hybrid_v.predict(
                    hybrid_v_scaler.transform(xv)
                )[0]
            ),
            float(
                hybrid_a.predict(
                    hybrid_a_scaler.transform(xa)
                )[0]
            ),
        )

    functions = {
        "traditional": predict_traditional,
        "mert": predict_mert,
        "hybrid": predict_hybrid,
    }

    rows = []

    print("===== CONTROLLED MODEL COMPARISON =====")
    print("Device:", device)
    print("Audio: TRAIN song 2")
    print("TEST partition used: NO")

    for repetition, order in enumerate(ORDERS, start=1):
        for mode in order:
            gc.collect()

            fn = functions[mode]

            for _ in range(WARMUP):
                fn()

            sync(device)

            cpu_before = process.cpu_times()
            wall_before = time.perf_counter()

            for run in range(1, RUNS + 1):
                sync(device)
                start = time.perf_counter()

                valence, arousal = fn()

                sync(device)
                elapsed_ms = (
                    time.perf_counter() - start
                ) * 1000

                assert np.isfinite(valence)
                assert np.isfinite(arousal)

                rows.append({
                    "repetition": repetition,
                    "mode": mode,
                    "run": run,
                    "latency_ms": elapsed_ms,
                    "valence": valence,
                    "arousal": arousal,
                    "device": str(device),
                    "test_used": False,
                })

            sync(device)

            wall_seconds = (
                time.perf_counter() - wall_before
            )

            cpu_after = process.cpu_times()

            cpu_seconds = (
                cpu_after.user - cpu_before.user
                + cpu_after.system - cpu_before.system
            )

            cpu_percent = (
                cpu_seconds / wall_seconds * 100
                if wall_seconds > 0 else 0.0
            )

            subset = pd.DataFrame(rows[-RUNS:])

            print(
                f"Rep {repetition} | {mode:11s} | "
                f"mean={subset['latency_ms'].mean():.3f} ms | "
                f"P95={subset['latency_ms'].quantile(0.95):.3f} ms | "
                f"CPU={cpu_percent:.2f}%"
            )

    df = pd.DataFrame(rows)

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(RESULT_PATH, index=False)

    print("\n===== OVERALL SUMMARY =====")

    for mode in functions:
        subset = df[df["mode"] == mode]

        print(
            f"{mode:11s} | "
            f"mean={subset['latency_ms'].mean():.3f} ms | "
            f"P95={subset['latency_ms'].quantile(0.95):.3f} ms"
        )

    print(
        "Process RSS at end:",
        f"{process.memory_info().rss / 1024**2:.2f} MB"
    )

    if device.type == "cuda":
        print(
            "GPU peak allocated:",
            f"{torch.cuda.max_memory_allocated(device) / 1024**2:.2f} MB"
        )

    print("Saved:", RESULT_PATH)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
