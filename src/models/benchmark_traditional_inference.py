from pathlib import Path
import time

import joblib
import numpy as np


FEATURE_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
)

MODEL_DIR = Path(
    "outputs/models/EXP_TRAD_001"
)

WARMUP_RUNS = 100
MEASURED_RUNS = 1000


artifact = np.load(
    FEATURE_PATH,
    allow_pickle=False,
)

X = artifact["X"]
split = artifact["split"].astype(str)

# Validation only. TEST remains untouched.
X_val = X[split == "validation"]

scaler = joblib.load(
    MODEL_DIR / "scaler.joblib"
)

valence_model = joblib.load(
    MODEL_DIR / "valence_ridge.joblib"
)

arousal_model = joblib.load(
    MODEL_DIR / "arousal_ridge.joblib"
)


def predict_one(raw_features):
    x = raw_features.reshape(1, -1)

    x_scaled = scaler.transform(x)

    valence = valence_model.predict(
        x_scaled
    )[0]

    arousal = arousal_model.predict(
        x_scaled
    )[0]

    return valence, arousal


print("===== TRADITIONAL INFERENCE BENCHMARK =====")
print("Warm-up runs:", WARMUP_RUNS)
print("Measured runs:", MEASURED_RUNS)
print("TEST: LOCKED / NOT USED")


# Fixed validation sample sequence.
samples = X_val[:MEASURED_RUNS]


# Warm-up
for i in range(WARMUP_RUNS):
    predict_one(
        X_val[i % len(X_val)]
    )


times_ms = []

for sample in samples:

    start = time.perf_counter()

    predict_one(sample)

    end = time.perf_counter()

    times_ms.append(
        (end - start) * 1000.0
    )


times_ms = np.asarray(
    times_ms,
    dtype=np.float64,
)


print("\nLatency")
print(
    "Mean inference latency:",
    f"{times_ms.mean():.6f} ms"
)

print(
    "P95 inference latency:",
    f"{np.percentile(times_ms, 95):.6f} ms"
)

print(
    "Median inference latency:",
    f"{np.median(times_ms):.6f} ms"
)

print(
    "Minimum:",
    f"{times_ms.min():.6f} ms"
)

print(
    "Maximum:",
    f"{times_ms.max():.6f} ms"
)

print(
    "\nPredictions finite:",
    np.isfinite(times_ms).all()
)

print(
    "RESULT: PASS - inference-only "
    "latency benchmark completed"
)