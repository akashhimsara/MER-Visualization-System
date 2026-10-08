
from pathlib import Path
import sys
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd


TARGET_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "deam_paired_va_targets_v1.csv"
)

CHUNK_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
    / "EXP_MERT_001"
    / "chunks"
)

LAYERS = (4, 8, 12)

EXPECTED_SPLITS = {
    "train": 88153,
    "validation": 19965,
}

EXPECTED_SONGS = 1531
EXPECTED_WINDOWS = 108118

REQUIRED_KEYS = {
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


print("===== MERT FULL CHUNK INTEGRITY AUDIT =====")

targets = pd.read_csv(TARGET_FILE)

# Do not extract or inspect TEST embeddings.
canonical = targets[
    targets["split"].isin(["train", "validation"])
].copy()

canonical = canonical.sort_values(
    ["song_id", "timestamp_ms"]
).reset_index(drop=True)

assert len(canonical) == EXPECTED_WINDOWS
assert canonical["song_id"].nunique() == EXPECTED_SONGS

assert (
    canonical["split"].value_counts().to_dict()
    == EXPECTED_SPLITS
)

expected_keys = set(
    zip(
        canonical["song_id"].astype(int),
        canonical["timestamp_ms"].astype(int),
    )
)

assert len(expected_keys) == EXPECTED_WINDOWS

chunk_files = sorted(
    CHUNK_DIR.glob("song_*.npz")
)

assert len(chunk_files) == EXPECTED_SONGS, (
    f"Expected {EXPECTED_SONGS} chunks, "
    f"found {len(chunk_files)}"
)

seen_keys = set()
split_counts = Counter()
song_ids = set()
total_rows = 0

for index, path in enumerate(chunk_files, start=1):

    with np.load(path, allow_pickle=False) as data:

        assert set(data.files) == REQUIRED_KEYS, path

        ids = data["song_id"]
        splits = data["split"]
        timestamps = data["timestamp_ms"]

        seconds = data["timestamp_sec"]
        valence = data["valence"]
        arousal = data["arousal"]

        n = len(ids)

        assert n > 0, path

        for arr in (
            splits,
            timestamps,
            seconds,
            valence,
            arousal,
        ):
            assert len(arr) == n, path

        unique_ids = np.unique(ids)

        assert len(unique_ids) == 1, path

        song_id = int(unique_ids[0])

        assert path.name == f"song_{song_id:04d}.npz"

        assert song_id not in song_ids
        song_ids.add(song_id)

        expected_song = canonical[
            canonical["song_id"] == song_id
        ].sort_values("timestamp_ms")

        assert len(expected_song) == n, path

        assert np.array_equal(
            ids,
            expected_song["song_id"].to_numpy(),
        ), path

        assert np.array_equal(
            timestamps,
            expected_song["timestamp_ms"].to_numpy(),
        ), path

        assert np.array_equal(
            splits,
            expected_song["split"].astype(str).to_numpy(),
        ), path

        for field, actual in (
            ("timestamp_sec", seconds),
            ("valence", valence),
            ("arousal", arousal),
        ):
            assert np.allclose(
                actual,
                expected_song[field].to_numpy(),
                rtol=0.0,
                atol=1e-6,
            ), (path, field)

        assert np.isfinite(seconds).all(), path
        assert np.isfinite(valence).all(), path
        assert np.isfinite(arousal).all(), path

        for layer in LAYERS:

            embedding = data[f"layer_{layer}"]

            assert embedding.shape == (n, 768), (
                path,
                layer,
                embedding.shape,
            )

            assert embedding.dtype == np.float32, (
                path,
                layer,
                embedding.dtype,
            )

            assert np.isfinite(embedding).all(), (
                path,
                layer,
            )

        for sid, timestamp, split in zip(
            ids, timestamps, splits
        ):
            key = (int(sid), int(timestamp))

            assert key not in seen_keys, (
                "Duplicate key",
                key,
            )

            seen_keys.add(key)

            assert split in EXPECTED_SPLITS, (
                "Unexpected split",
                split,
            )

            split_counts[str(split)] += 1

        total_rows += n

    if index % 250 == 0:
        print(
            f"Validated {index}/{EXPECTED_SONGS} "
            f"song chunks"
        )


assert total_rows == EXPECTED_WINDOWS
assert len(seen_keys) == EXPECTED_WINDOWS
assert seen_keys == expected_keys

assert dict(split_counts) == EXPECTED_SPLITS

assert len(song_ids) == EXPECTED_SONGS

assert not list(CHUNK_DIR.glob("*.tmp.npz"))

print()
print("===== AUDIT SUMMARY =====")
print("Validated song chunks:", len(song_ids))
print("Validated total windows:", total_rows)
print("TRAIN windows:", split_counts["train"])
print("VALIDATION windows:", split_counts["validation"])
print("Unique canonical keys:", len(seen_keys))
print("Embedding layers:", LAYERS)
print("Embedding dimension:", 768)
print("Duplicate keys: 0")
print("Missing canonical keys: 0")
print("Non-finite embeddings: 0")
print("TEST partition used: NO")
print("RESULT: PASS")
