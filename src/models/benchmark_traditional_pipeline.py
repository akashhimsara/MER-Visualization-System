from pathlib import Path
import sys
import time

import joblib
import librosa
import numpy as np
import psutil



PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.features.traditional_features import (
    extract_traditional_features,
)


AUDIO_PATH = Path(
    "data/raw/deam/MEMD_audio/2.mp3"
)

MODEL_DIR = Path(
    "outputs/models/EXP_TRAD_001"
)

WARMUP_RUNS = 5
MEASURED_RUNS = 50

TARGET_TIMES = np.arange(
    20.0,
    20.0 + MEASURED_RUNS * 0.5,
    0.5,
)


scaler = joblib.load(
    MODEL_DIR / "scaler.joblib"
)

valence_model = joblib.load(
    MODEL_DIR / "valence_ridge.joblib"
)

arousal_model = joblib.load(
    MODEL_DIR / "arousal_ridge.joblib"
)

process = psutil.Process()


def run_pipeline(target_time):

    feature_start = time.perf_counter()

    features = extract_traditional_features(
        AUDIO_PATH,
        float(target_time),
    )

    feature_end = time.perf_counter()

    x = features.reshape(1, -1)

    inference_start = time.perf_counter()

    x_scaled = scaler.transform(x)

    valence = valence_model.predict(
        x_scaled
    )[0]

    arousal = arousal_model.predict(
        x_scaled
    )[0]

    inference_end = time.perf_counter()

    feature_ms = (
        feature_end - feature_start
    ) * 1000.0

    inference_ms = (
        inference_end - inference_start
    ) * 1000.0

    total_ms = (
        inference_end - feature_start
    ) * 1000.0

    return (
        feature_ms,
        inference_ms,
        total_ms,
        valence,
        arousal,
    )


print(
    "===== TRADITIONAL END-TO-END BENCHMARK ====="
)

print("Audio:", AUDIO_PATH)
print("Warm-up runs:", WARMUP_RUNS)
print("Measured runs:", MEASURED_RUNS)
print("TEST: LOCKED / NOT USED")


# ---------------------------------------------------------
# Warm-up
# ---------------------------------------------------------

for i in range(WARMUP_RUNS):
    run_pipeline(
        TARGET_TIMES[
            i % len(TARGET_TIMES)
        ]
    )


# ---------------------------------------------------------
# Measurement
# ---------------------------------------------------------

feature_times = []
inference_times = []
total_times = []
cpu_samples = []

peak_rss = process.memory_info().rss


for target_time in TARGET_TIMES:

    cpu_before = process.cpu_times()
    wall_before = time.perf_counter()

    (
        feature_ms,
        inference_ms,
        total_ms,
        valence,
        arousal,
    ) = run_pipeline(target_time)

    wall_after = time.perf_counter()
    cpu_after = process.cpu_times()

    cpu_seconds = (
        (cpu_after.user - cpu_before.user)
        + (cpu_after.system - cpu_before.system)
    )

    wall_seconds = (
        wall_after - wall_before
    )

    if wall_seconds > 0:
        cpu_percent = (
            cpu_seconds
            / wall_seconds
        ) * 100.0
    else:
        cpu_percent = 0.0

    cpu_samples.append(cpu_percent)

    feature_times.append(feature_ms)
    inference_times.append(inference_ms)
    total_times.append(total_ms)

    peak_rss = max(
        peak_rss,
        process.memory_info().rss,
    )

    if not (
        np.isfinite(valence)
        and np.isfinite(arousal)
    ):
        raise ValueError(
            "Non-finite prediction"
        )


feature_times = np.asarray(feature_times)
inference_times = np.asarray(inference_times)
total_times = np.asarray(total_times)
cpu_samples = np.asarray(cpu_samples)


print("\nFeature extraction latency")
print(
    "Mean:",
    f"{feature_times.mean():.3f} ms"
)
print(
    "P95:",
    f"{np.percentile(feature_times, 95):.3f} ms"
)


print("\nModel inference latency")
print(
    "Mean:",
    f"{inference_times.mean():.3f} ms"
)
print(
    "P95:",
    f"{np.percentile(inference_times, 95):.3f} ms"
)


print("\nEnd-to-end processing latency")
print(
    "Mean:",
    f"{total_times.mean():.3f} ms"
)
print(
    "P95:",
    f"{np.percentile(total_times, 95):.3f} ms"
)


print("\nProcess resources")
print(
    "Average CPU:",
    f"{cpu_samples.mean():.2f}%"
)
print(
    "Peak observed CPU:",
    f"{cpu_samples.max():.2f}%"
)
print(
    "Peak process RSS:",
    f"{peak_rss / (1024 ** 2):.2f} MB"
)


print(
    "\nRESULT: PASS - traditional pipeline "
    "benchmark completed"
)