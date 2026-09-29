from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.features.traditional_features import (
    extract_traditional_features,
)


TARGET_PATH = Path(
    "data/processed/deam_paired_va_targets_v1.csv"
)

AUDIO_DIR = Path(
    "data/raw/deam/MEMD_audio"
)

# Small controlled smoke batch
NUM_SONGS = 5
TARGETS_PER_SONG = 3


targets = pd.read_csv(TARGET_PATH)

selected_song_ids = (
    targets["song_id"]
    .drop_duplicates()
    .sort_values()
    .head(NUM_SONGS)
    .tolist()
)

tested = 0
failures = []


print("===== TRADITIONAL FEATURE BATCH TEST =====")
print("Songs selected:", selected_song_ids)


for song_id in selected_song_ids:

    song_targets = (
        targets[
            targets["song_id"] == song_id
        ]
        .sort_values("timestamp_sec")
        .head(TARGETS_PER_SONG)
    )

    audio_path = (
        AUDIO_DIR / f"{song_id}.mp3"
    )

    for row in song_targets.itertuples():

        timestamp = float(
            row.timestamp_sec
        )

        try:
            features = (
                extract_traditional_features(
                    audio_path,
                    timestamp,
                )
            )

            valid = (
                features.shape == (86,)
                and features.dtype == np.float32
                and np.isfinite(features).all()
            )

            if not valid:
                failures.append(
                    (
                        song_id,
                        timestamp,
                        "invalid feature vector",
                    )
                )

            else:
                tested += 1

                print(
                    f"PASS | song={song_id} "
                    f"| t={timestamp:.1f}s "
                    f"| shape={features.shape}"
                )

        except Exception as exc:

            failures.append(
                (
                    song_id,
                    timestamp,
                    str(exc),
                )
            )


print("\nSummary")
print("Successful windows:", tested)
print("Failures:", len(failures))


if failures:

    print("\nFailure details:")

    for failure in failures:
        print(failure)

    print("\nRESULT: REVIEW REQUIRED")

else:

    expected = (
        NUM_SONGS
        * TARGETS_PER_SONG
    )

    if tested == expected:

        print(
            "\nRESULT: PASS - all small-batch "
            "traditional feature windows are valid"
        )

    else:

        print(
            "\nRESULT: REVIEW REQUIRED - "
            "unexpected number of windows"
        )