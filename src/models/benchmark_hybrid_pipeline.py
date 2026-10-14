
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
MODELS_DIR = ROOT / "outputs/models/EXP_HYBRID_001"
AUDIO_PATH = ROOT / "data/raw/deam/MEMD_audio/2.mp3"

RESULT_PATH = (
    ROOT / "outputs/results/"
    "EXP_HYBRID_001_prepared_window_benchmark.csv"
)

TRAD_SR = 22050
MERT_SR = 24000
CONTEXT_SECONDS = 5.0
TARGET_TIME = 20.0

WARMUP = 10
RUNS = 50
REPETITIONS = 3


def sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def load_window(sample_rate):
    waveform, sr = librosa.load(
        AUDIO_PATH,
        sr=sample_rate,
        mono=True,
        offset=TARGET_TIME - CONTEXT_SECONDS,
        duration=CONTEXT_SECONDS,
    )

    expected = int(round(CONTEXT_SECONDS * sample_rate))

    if abs(len(waveform) - expected) > 1:
        raise ValueError(
            f"Unexpected window length: {len(waveform)}"
        )

    if len(waveform) > expected:
        waveform = waveform[:expected]
    elif len(waveform) < expected:
        waveform = np.pad(
            waveform,
            (0, expected - len(waveform)),
        )

    if sr != sample_rate:
        raise ValueError("Sample rate mismatch")

    if not np.isfinite(waveform).all():
        raise ValueError("Non-finite audio")

    return waveform.astype(np.float32)


def main():
    assert AUDIO_PATH.exists(), "TRAIN audio missing"

    torch.set_num_threads(4)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    process = psutil.Process()

    trad_waveform = load_window(TRAD_SR)
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

    valence_scaler = joblib.load(
        MODELS_DIR / "layer_4/scaler.joblib"
    )
    valence_model = joblib.load(
        MODELS_DIR / "layer_4/valence_ridge.joblib"
    )

    arousal_scaler = joblib.load(
        MODELS_DIR / "layer_8/scaler.joblib"
    )
    arousal_model = joblib.load(
        MODELS_DIR / "layer_8/arousal_ridge.joblib"
    )

    assert valence_scaler.n_features_in_ == 854
    assert arousal_scaler.n_features_in_ == 854

    def run_once():
        sync(device)
        start = time.perf_counter()

        traditional = extract_traditional_waveform_features(
            trad_waveform,
            TRAD_SR,
        )

        sync(device)
        after_traditional = time.perf_counter()

        embeddings = extract_mert_early_exit_safe(
            waveform=mert_waveform,
            model=mert_model,
            processor=processor,
            device=device,
            sample_rate=MERT_SR,
            exit_layer=8,
            requested_layers=(4, 8),
        )

        sync(device)
        after_mert = time.perf_counter()

        assert traditional.shape == (86,)
        assert embeddings[4].shape == (768,)
        assert embeddings[8].shape == (768,)

        x_valence = np.concatenate([
            traditional,
            embeddings[4],
        ]).reshape(1, -1)

        x_arousal = np.concatenate([
            traditional,
            embeddings[8],
        ]).reshape(1, -1)

        valence = valence_model.predict(
            valence_scaler.transform(x_valence)
        )[0]

        arousal = arousal_model.predict(
            arousal_scaler.transform(x_arousal)
        )[0]

        after_ridge = time.perf_counter()

        if not (
            np.isfinite(valence)
            and np.isfinite(arousal)
        ):
            raise ValueError("Non-finite VA predictions")

        return {
            "traditional_ms": (
                after_traditional - start
            ) * 1000,
            "mert_safe_ms": (
                after_mert - after_traditional
            ) * 1000,
            "ridge_ms": (
                after_ridge - after_mert
            ) * 1000,
            "total_ms": (
                after_ridge - start
            ) * 1000,
            "valence": float(valence),
            "arousal": float(arousal),
        }

    print("===== HYBRID PREPARED-WINDOW BENCHMARK =====")
    print("Device:", device)
    print("Audio: TRAIN song 2")
    print("Window: [15.0s, 20.0s]")
    print("TEST partition used: NO")

    rows = []

    for repetition in range(1, REPETITIONS + 1):
        gc.collect()

        for _ in range(WARMUP):
            run_once()

        sync(device)
        cpu_before = process.cpu_times()
        wall_before = time.perf_counter()

        for run in range(1, RUNS + 1):
            measurement = run_once()
            rows.append({
                "repetition": repetition,
                "run": run,
                "device": str(device),
                **measurement,
                "test_used": False,
            })

        sync(device)
        wall_seconds = time.perf_counter() - wall_before
        cpu_after = process.cpu_times()

        cpu_seconds = (
            cpu_after.user - cpu_before.user
            + cpu_after.system - cpu_before.system
        )

        cpu_percent = (
            cpu_seconds / wall_seconds * 100
            if wall_seconds > 0 else 0.0
        )

        subset = pd.DataFrame(
            rows[-RUNS:]
        )

        print(
            f"Rep {repetition}: "
            f"mean={subset['total_ms'].mean():.3f} ms | "
            f"P95={subset['total_ms'].quantile(0.95):.3f} ms | "
            f"CPU={cpu_percent:.2f}%"
        )

    df = pd.DataFrame(rows)

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(RESULT_PATH, index=False)

    print("\n===== LATENCY SUMMARY =====")

    for column in (
        "traditional_ms",
        "mert_safe_ms",
        "ridge_ms",
        "total_ms",
    ):
        print(
            f"{column}: "
            f"mean={df[column].mean():.3f} ms | "
            f"P95={df[column].quantile(0.95):.3f} ms"
        )

    print(
        "Process RSS:",
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
