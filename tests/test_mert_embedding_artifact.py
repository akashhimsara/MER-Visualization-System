from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd


ARTIFACT = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
    / "EXP_MERT_001"
    / "mert_embeddings_checkpoint.npz"
)

TARGET_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "deam_paired_va_targets_v1.csv"
)


print("===== MERT PILOT ARTIFACT INTEGRITY TEST =====")


# --------------------------------------------------
# Load artifact safely
# --------------------------------------------------

data = np.load(
    ARTIFACT,
    allow_pickle=False,
)

print("Artifact keys:", data.files)


required_keys = {
    "song_id",
    "split",
    "timestamp_ms",
    "timestamp_sec",
    "valence",
    "arousal",
    "layer_4",
    "layer_8",
    "layer_12",
}

assert set(data.files) == required_keys


# --------------------------------------------------
# Shape validation
# --------------------------------------------------

n = len(data["song_id"])

print("Rows:", n)

assert n > 0
print("Validated artifact rows:", n)

for key in [
    "song_id",
    "split",
    "timestamp_ms",
    "timestamp_sec",
    "valence",
    "arousal",
]:
    print(
        f"{key}:",
        data[key].shape,
        data[key].dtype,
    )

    assert data[key].shape == (n,)


for layer in [4, 8, 12]:

    arr = data[f"layer_{layer}"]

    print(
        f"layer_{layer}:",
        arr.shape,
        arr.dtype,
        "finite=",
        np.isfinite(arr).all(),
    )

    assert arr.shape == (n, 768)
    assert arr.dtype == np.float32
    assert np.isfinite(arr).all()


# --------------------------------------------------
# TEST lock
# --------------------------------------------------

splits = data["split"]

print(
    "Split values:",
    np.unique(splits),
)

assert not np.any(splits == "test")


# --------------------------------------------------
# Canonical metadata alignment
# --------------------------------------------------

targets = pd.read_csv(TARGET_FILE)

targets = targets[
    targets["split"].isin(
        ["train", "validation"]
    )
].copy()

targets = targets.sort_values(
    ["song_id", "timestamp_ms"]
).reset_index(drop=True)

expected = targets.head(n)


assert np.array_equal(
    data["song_id"],
    expected["song_id"].to_numpy(
        dtype=np.int32
    ),
)

assert np.array_equal(
    data["timestamp_ms"],
    expected["timestamp_ms"].to_numpy(
        dtype=np.int64
    ),
)

assert np.array_equal(
    data["split"],
    expected["split"].astype(
        str
    ).to_numpy(),
)

assert np.allclose(
    data["timestamp_sec"],
    expected["timestamp_sec"].to_numpy(
        dtype=np.float32
    ),
)

assert np.allclose(
    data["valence"],
    expected["valence"].to_numpy(
        dtype=np.float32
    ),
)

assert np.allclose(
    data["arousal"],
    expected["arousal"].to_numpy(
        dtype=np.float32
    ),
)


# --------------------------------------------------
# Duplicate key validation
# --------------------------------------------------

keys = list(
    zip(
        data["song_id"].tolist(),
        data["timestamp_ms"].tolist(),
    )
)

assert len(keys) == len(set(keys))


print()
print("Canonical metadata alignment: PASS")
print("Duplicate song/timestamp keys: 0")
print("TEST partition used: NO")

print()
print("RESULT: PASS")
print(
    "Pilot MERT artifact is structurally valid, "
    "finite, and aligned with canonical DEAM targets."
)