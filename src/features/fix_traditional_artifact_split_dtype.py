from pathlib import Path
import hashlib

import numpy as np


ARTIFACT_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
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


print("===== FIX TRADITIONAL ARTIFACT SPLIT DTYPE =====")

# This one-time load is required because the original artifact
# stored split labels as an object array.
old = np.load(
    ARTIFACT_PATH,
    allow_pickle=True,
)

X = old["X"]
song_id = old["song_id"]
timestamp_ms = old["timestamp_ms"]
valence = old["valence"]
arousal = old["arousal"]

split = old["split"].astype("U10")

print("Original feature shape:", X.shape)
print("Converted split dtype:", split.dtype)

# Write to temporary file first.
temp_path = ARTIFACT_PATH.with_name(
    "deam_traditional_features_v1_fixed.npz"
)

np.savez_compressed(
    temp_path,
    X=X,
    song_id=song_id,
    timestamp_ms=timestamp_ms,
    valence=valence,
    arousal=arousal,
    split=split,
)

# Verify that the new file is readable WITHOUT pickle.
check = np.load(
    temp_path,
    allow_pickle=False,
)

print("Reloaded X shape:", check["X"].shape)
print("Reloaded split dtype:", check["split"].dtype)
print(
    "Reloaded split values:",
    np.unique(check["split"]),
)

check.close()
old.close()

# Replace original only after successful verification.
temp_path.replace(ARTIFACT_PATH)

print("\nArtifact replaced successfully.")
print("New SHA256:", sha256_file(ARTIFACT_PATH))

print(
    "\nRESULT: PASS - split metadata converted "
    "to non-object Unicode representation"
)