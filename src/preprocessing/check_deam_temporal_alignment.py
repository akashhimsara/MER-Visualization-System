from pathlib import Path

import librosa
import pandas as pd


BASE = Path("data/raw/deam")

AUDIO_DIR = BASE / "MEMD_audio"

AROUSAL_PATH = (
    BASE
    / "annotations"
    / "annotations averaged per song"
    / "dynamic (per second annotations)"
    / "arousal.csv"
)

VALENCE_PATH = (
    BASE
    / "annotations"
    / "annotations averaged per song"
    / "dynamic (per second annotations)"
    / "valence.csv"
)


def timestamp_ms(column):
    return int(
        column.replace("sample_", "").replace("ms", "")
    )


print("===== DEAM AUDIO ↔ ANNOTATION TEMPORAL ALIGNMENT =====")

arousal = pd.read_csv(AROUSAL_PATH)
valence = pd.read_csv(VALENCE_PATH)

a_cols = [
    c for c in arousal.columns
    if c.startswith("sample_")
]

v_cols = [
    c for c in valence.columns
    if c.startswith("sample_")
]

common_cols = [
    c for c in a_cols
    if c in set(v_cols)
]

# Index by song ID for safe matching
arousal = arousal.set_index("song_id")
valence = valence.set_index("song_id")

violations = []
records = []

for count, song_id in enumerate(arousal.index, start=1):

    audio_path = AUDIO_DIR / f"{song_id}.mp3"

    # Fast metadata-based duration check.
    duration = librosa.get_duration(path=audio_path)

    a_row = arousal.loc[song_id, common_cols]
    v_row = valence.loc[song_id, common_cols]

    # A usable MER target requires BOTH V and A.
    paired_valid = a_row.notna() & v_row.notna()

    valid_cols = [
        col
        for col in common_cols
        if paired_valid[col]
    ]

    if not valid_cols:
        violations.append(
            (song_id, "NO_PAIRED_TARGETS")
        )
        continue

    first_target = timestamp_ms(valid_cols[0]) / 1000.0
    last_target = timestamp_ms(valid_cols[-1]) / 1000.0

    margin = duration - last_target

    records.append(
        {
            "song_id": song_id,
            "audio_duration": duration,
            "first_paired_target": first_target,
            "last_paired_target": last_target,
            "margin_seconds": margin,
            "paired_target_count": len(valid_cols),
        }
    )

    if first_target < 0 or last_target > duration:
        violations.append(
            (
                song_id,
                f"duration={duration:.3f}, "
                f"last_target={last_target:.3f}"
            )
        )

    if count % 200 == 0:
        print(f"Checked {count}/1802 songs...")


results = pd.DataFrame(records)

print("\n===== RESULTS =====")

print("Songs checked:", len(results))
print("Temporal violations:", len(violations))

print(
    "First paired target min/max:",
    results["first_paired_target"].min(),
    results["first_paired_target"].max()
)

print(
    "Last paired target min/max:",
    results["last_paired_target"].min(),
    results["last_paired_target"].max()
)

print(
    "Paired targets per song min/max:",
    int(results["paired_target_count"].min()),
    int(results["paired_target_count"].max())
)

print("\nAudio minus last-target margin:")

print(
    "Minimum margin:",
    f'{results["margin_seconds"].min():.3f} s'
)

print(
    "Maximum margin:",
    f'{results["margin_seconds"].max():.3f} s'
)

print(
    "Mean margin:",
    f'{results["margin_seconds"].mean():.3f} s'
)

if violations:
    print("\nViolations:")

    for item in violations:
        print(item)

    print("\nRESULT: REVIEW REQUIRED")

else:
    print(
        "\nRESULT: PASS - every paired V/A target "
        "lies within its corresponding audio duration"
    )


print("\nShortest margins:")

print(
    results.nsmallest(
        10,
        "margin_seconds"
    )[
        [
            "song_id",
            "audio_duration",
            "last_paired_target",
            "margin_seconds",
            "paired_target_count",
        ]
    ].to_string(index=False)
)