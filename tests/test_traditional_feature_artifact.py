from pathlib import Path
import hashlib

import numpy as np
import pandas as pd


FEATURE_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
)

TARGET_PATH = Path(
    "data/processed/deam_paired_va_targets_v1.csv"
)


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


print("===== TRADITIONAL FEATURE ARTIFACT INTEGRITY TEST =====")

# ---------------------------------------------------------
# Load canonical target manifest
# ---------------------------------------------------------

targets = pd.read_csv(TARGET_PATH)

targets = targets.sort_values(
    ["song_id", "timestamp_ms"]
).reset_index(drop=True)


# ---------------------------------------------------------
# Load saved feature artifact
# ---------------------------------------------------------

artifact = np.load(
    FEATURE_PATH,
    allow_pickle=False,
)

X = artifact["X"]
song_id = artifact["song_id"]
timestamp_ms = artifact["timestamp_ms"]
valence = artifact["valence"]
arousal = artifact["arousal"]
split = artifact["split"]


# ---------------------------------------------------------
# Basic structure
# ---------------------------------------------------------

print("\nArtifact structure")
print("X shape:", X.shape)
print("X dtype:", X.dtype)
print("Finite X:", np.isfinite(X).all())

print("song_id shape:", song_id.shape)
print("timestamp_ms shape:", timestamp_ms.shape)
print("valence shape:", valence.shape)
print("arousal shape:", arousal.shape)
print("split shape:", split.shape)


# ---------------------------------------------------------
# Exact metadata alignment
# ---------------------------------------------------------

song_match = np.array_equal(
    song_id,
    targets["song_id"].to_numpy(
        dtype=np.int32
    ),
)

timestamp_match = np.array_equal(
    timestamp_ms,
    targets["timestamp_ms"].to_numpy(
        dtype=np.int32
    ),
)

split_match = np.array_equal(
    split.astype(str),
    targets["split"].astype(str).to_numpy(),
)


# Float targets were intentionally stored as float32.
# Compare against canonical targets after the same cast.

valence_match = np.array_equal(
    valence,
    targets["valence"].to_numpy(
        dtype=np.float32
    ),
)

arousal_match = np.array_equal(
    arousal,
    targets["arousal"].to_numpy(
        dtype=np.float32
    ),
)


print("\nCanonical alignment")
print("Song IDs exact match:", song_match)
print("Timestamps exact match:", timestamp_match)
print("Split labels exact match:", split_match)
print("Valence exact float32 match:", valence_match)
print("Arousal exact float32 match:", arousal_match)


# ---------------------------------------------------------
# Split counts
# ---------------------------------------------------------

unique_splits, split_counts = np.unique(
    split.astype(str),
    return_counts=True,
)

print("\nFeature rows by split")

for name, count in zip(
    unique_splits,
    split_counts,
):
    print(f"{name}: {count}")


# ---------------------------------------------------------
# Artifact checksum
# ---------------------------------------------------------

checksum = sha256_file(FEATURE_PATH)

print("\nSHA256:", checksum)


# ---------------------------------------------------------
# Final decision
# ---------------------------------------------------------

all_valid = all(
    [
        X.shape == (129995, 86),
        X.dtype == np.float32,
        np.isfinite(X).all(),
        song_match,
        timestamp_match,
        split_match,
        valence_match,
        arousal_match,
    ]
)

if all_valid:
    print(
        "\nRESULT: PASS - saved traditional feature "
        "artifact exactly aligns with canonical targets"
    )
else:
    print("\nRESULT: REVIEW REQUIRED")