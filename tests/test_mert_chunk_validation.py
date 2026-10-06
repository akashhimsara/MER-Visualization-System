from pathlib import Path
import shutil
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.features.extract_deam_mert_embeddings_chunked import (
    TARGET_FILE,
    chunk_path,
    validate_chunk,
)


print("===== MERT CHUNK VALIDATION TEST =====")

targets = pd.read_csv(TARGET_FILE)

targets = targets[
    targets["split"].isin(
        ["train", "validation"]
    )
].copy()

song_id = 2

song_targets = targets[
    targets["song_id"] == song_id
].copy()

assert len(song_targets) > 0
assert not (song_targets["split"] == "test").any()

source_chunk = chunk_path(song_id)

assert source_chunk.exists(), (
    f"Pilot chunk missing: {source_chunk}"
)


# --------------------------------------------------
# 1. Original valid chunk
# --------------------------------------------------

valid, message = validate_chunk(
    source_chunk,
    song_targets,
)

print(
    "Original chunk:",
    valid,
    "|",
    message,
)

assert valid


# --------------------------------------------------
# 2. Corrupted COPY only
# --------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:

    corrupt_copy = (
        Path(temp_dir)
        / "song_0002_corrupt.npz"
    )

    shutil.copy2(
        source_chunk,
        corrupt_copy,
    )

    original_size = corrupt_copy.stat().st_size

    # Truncate the COPY.
    # The real chunk is never modified.
    with open(corrupt_copy, "r+b") as f:
        f.truncate(
            max(
                1,
                original_size // 2,
            )
        )

    valid_corrupt, corrupt_message = (
        validate_chunk(
            corrupt_copy,
            song_targets,
        )
    )

    print(
        "Corrupted copy:",
        valid_corrupt,
        "|",
        corrupt_message,
    )

    assert not valid_corrupt


# --------------------------------------------------
# 3. Re-check real chunk
# --------------------------------------------------

valid_again, message_again = validate_chunk(
    source_chunk,
    song_targets,
)

print(
    "Original chunk after test:",
    valid_again,
    "|",
    message_again,
)

assert valid_again


print("TEST partition used: NO")
print(
    "RESULT: PASS - corrupt chunk is rejected "
    "without modifying the real artifact"
)