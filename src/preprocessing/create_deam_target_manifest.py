from pathlib import Path
import hashlib

import pandas as pd


BASE = Path("data/raw/deam")

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

SPLIT_PATH = Path(
    "data/splits/deam_song_split_v1.csv"
)

OUTPUT_DIR = Path("data/processed")

OUTPUT_PATH = (
    OUTPUT_DIR
    / "deam_paired_va_targets_v1.csv"
)


print("===== CREATE DEAM PAIRED VA TARGET MANIFEST =====")

arousal = pd.read_csv(AROUSAL_PATH)
valence = pd.read_csv(VALENCE_PATH)
splits = pd.read_csv(SPLIT_PATH)


# ---------------------------------------------------------
# Identify shared timestamp columns
# ---------------------------------------------------------

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

print("\nShared timestamp columns:", len(common_cols))


# ---------------------------------------------------------
# Convert wide annotations to long format
# ---------------------------------------------------------

a_long = arousal[
    ["song_id"] + common_cols
].melt(
    id_vars="song_id",
    var_name="timestamp",
    value_name="arousal"
)

v_long = valence[
    ["song_id"] + common_cols
].melt(
    id_vars="song_id",
    var_name="timestamp",
    value_name="valence"
)


# ---------------------------------------------------------
# Merge V/A using exact song + timestamp identity
# ---------------------------------------------------------

targets = a_long.merge(
    v_long,
    on=["song_id", "timestamp"],
    how="inner",
    validate="one_to_one"
)

raw_merged_rows = len(targets)

# Paired target rule:
# BOTH Valence and Arousal must exist.
targets = targets.dropna(
    subset=["valence", "arousal"]
).copy()


# ---------------------------------------------------------
# Parse timestamp
# ---------------------------------------------------------

targets["timestamp_ms"] = (
    targets["timestamp"]
    .str.replace("sample_", "", regex=False)
    .str.replace("ms", "", regex=False)
    .astype(int)
)

targets["timestamp_sec"] = (
    targets["timestamp_ms"] / 1000.0
)


# ---------------------------------------------------------
# Attach frozen song-level split
# ---------------------------------------------------------

targets = targets.merge(
    splits,
    on="song_id",
    how="left",
    validate="many_to_one"
)

if targets["split"].isna().any():
    raise ValueError(
        "At least one target row has no canonical split"
    )


# ---------------------------------------------------------
# Canonical ordering
# ---------------------------------------------------------

targets = targets[
    [
        "song_id",
        "split",
        "timestamp_ms",
        "timestamp_sec",
        "valence",
        "arousal",
    ]
]

targets = targets.sort_values(
    ["song_id", "timestamp_ms"]
).reset_index(drop=True)


# ---------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------

duplicate_count = int(
    targets.duplicated(
        subset=["song_id", "timestamp_ms"]
    ).sum()
)

missing_target_cells = int(
    targets[["valence", "arousal"]]
    .isna()
    .sum()
    .sum()
)

timestamps = (
    targets.groupby("song_id")["timestamp_ms"]
    .apply(list)
)

bad_step_songs = []

for song_id, times in timestamps.items():

    if len(times) <= 1:
        continue

    steps = [
        b - a
        for a, b in zip(times[:-1], times[1:])
    ]

    if any(step != 500 for step in steps):
        bad_step_songs.append(song_id)


split_song_overlap = {}

split_song_sets = {
    name: set(
        targets.loc[
            targets["split"] == name,
            "song_id"
        ]
    )
    for name in ["train", "validation", "test"]
}

split_song_overlap["train_validation"] = len(
    split_song_sets["train"]
    & split_song_sets["validation"]
)

split_song_overlap["train_test"] = len(
    split_song_sets["train"]
    & split_song_sets["test"]
)

split_song_overlap["validation_test"] = len(
    split_song_sets["validation"]
    & split_song_sets["test"]
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

targets.to_csv(
    OUTPUT_PATH,
    index=False
)


# ---------------------------------------------------------
# SHA256
# ---------------------------------------------------------

sha256 = hashlib.sha256(
    OUTPUT_PATH.read_bytes()
).hexdigest()


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

print("\nRows")
print("Raw merged V/A cells:", raw_merged_rows)
print("Usable paired VA rows:", len(targets))

print("\nSongs")
print("Unique songs:", targets["song_id"].nunique())

print("\nTarget integrity")
print("Duplicate song/timestamp rows:", duplicate_count)
print("Missing V/A cells:", missing_target_cells)
print("Songs with non-500ms internal steps:", len(bad_step_songs))

print("\nTimestamp range")
print(
    "Minimum:",
    targets["timestamp_sec"].min()
)
print(
    "Maximum:",
    targets["timestamp_sec"].max()
)

print("\nSplit target rows")
print(
    targets["split"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nSplit unique songs")
print(
    targets.groupby("split")["song_id"]
    .nunique()
    .sort_index()
    .to_string()
)

print("\nCross-split song overlap")
for name, count in split_song_overlap.items():
    print(f"{name}: {count}")

print("\nOutput:")
print(OUTPUT_PATH)

print("\nSHA256:")
print(sha256)


passed = (
    targets["song_id"].nunique() == 1802
    and duplicate_count == 0
    and missing_target_cells == 0
    and len(bad_step_songs) == 0
    and all(
        count == 0
        for count in split_song_overlap.values()
    )
)

if passed:
    print(
        "\nRESULT: PASS - canonical paired VA "
        "target manifest created"
    )
else:
    print("\nRESULT: REVIEW REQUIRED")