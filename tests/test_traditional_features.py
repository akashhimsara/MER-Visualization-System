from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.features.traditional_features import (
    extract_traditional_features,
)


AUDIO_PATH = Path(
    "data/raw/deam/MEMD_audio/2.mp3"
)

TARGET_TIME = 20.0


print("===== TRADITIONAL FEATURE SMOKE TEST =====")

features = extract_traditional_features(
    AUDIO_PATH,
    TARGET_TIME,
)

print("Audio:", AUDIO_PATH)
print("Target timestamp:", TARGET_TIME)
print("Context:", "[15.0 s, 20.0 s]")

print("\nFeature vector")
print("Shape:", features.shape)
print("Dtype:", features.dtype)
print("Finite values:", np.isfinite(features).all())

print("\nSummary")
print("Minimum:", float(features.min()))
print("Maximum:", float(features.max()))
print("Mean:", float(features.mean()))

if (
    features.shape == (86,)
    and features.dtype == np.float32
    and np.isfinite(features).all()
):
    print(
        "\nRESULT: PASS - traditional "
        "86-dimensional feature vector generated"
    )
else:
    print("\nRESULT: REVIEW REQUIRED")