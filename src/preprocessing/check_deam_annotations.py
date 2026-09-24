from pathlib import Path
import pandas as pd
import re

BASE = Path("data/raw/deam")

AROUSAL = (
    BASE
    / "annotations"
    / "annotations averaged per song"
    / "dynamic (per second annotations)"
    / "arousal.csv"
)

VALENCE = (
    BASE
    / "annotations"
    / "annotations averaged per song"
    / "dynamic (per second annotations)"
    / "valence.csv"
)


def timestamp_columns(df):
    return [c for c in df.columns if c.startswith("sample_")]


def timestamp_ms(column):
    match = re.fullmatch(r"sample_(\d+)ms", column)

    if not match:
        raise ValueError(f"Unexpected timestamp column: {column}")

    return int(match.group(1))


print("===== DEAM DYNAMIC ANNOTATION INTEGRITY CHECK =====")

arousal = pd.read_csv(AROUSAL)
valence = pd.read_csv(VALENCE)

print("\nShapes")
print("Arousal:", arousal.shape)
print("Valence:", valence.shape)

a_cols = timestamp_columns(arousal)
v_cols = timestamp_columns(valence)

a_times = [timestamp_ms(c) for c in a_cols]
v_times = [timestamp_ms(c) for c in v_cols]

print("\nTimestamp columns")
print("Arousal timestamp columns:", len(a_cols))
print("Valence timestamp columns:", len(v_cols))

print("\nTimestamp range")
print(
    "Arousal:",
    min(a_times) / 1000,
    "to",
    max(a_times) / 1000,
    "seconds"
)
print(
    "Valence:",
    min(v_times) / 1000,
    "to",
    max(v_times) / 1000,
    "seconds"
)

a_steps = sorted(set(
    b - a for a, b in zip(a_times[:-1], a_times[1:])
))

v_steps = sorted(set(
    b - a for a, b in zip(v_times[:-1], v_times[1:])
))

print("\nTimestamp increments")
print("Arousal increments (ms):", a_steps)
print("Valence increments (ms):", v_steps)

print("\nID integrity")
print("Arousal unique song IDs:", arousal["song_id"].nunique())
print("Valence unique song IDs:", valence["song_id"].nunique())

print(
    "Same song ID order:",
    arousal["song_id"].tolist() == valence["song_id"].tolist()
)

print("\nCross-target timestamp consistency")
print("Same timestamp columns:", a_cols == v_cols)

a_values = arousal[a_cols]
v_values = valence[v_cols]

print("\nMissing values")
print("Arousal NaN cells:", int(a_values.isna().sum().sum()))
print("Valence NaN cells:", int(v_values.isna().sum().sum()))

print(
    "Arousal rows containing >=1 NaN:",
    int(a_values.isna().any(axis=1).sum())
)

print(
    "Valence rows containing >=1 NaN:",
    int(v_values.isna().any(axis=1).sum())
)

# Number of valid dynamic targets available for each song
a_valid = a_values.notna().sum(axis=1)
v_valid = v_values.notna().sum(axis=1)

print("\nValid annotation counts per song")

print(
    "Arousal min/max:",
    int(a_valid.min()),
    int(a_valid.max())
)

print(
    "Valence min/max:",
    int(v_valid.min()),
    int(v_valid.max())
)


# ---------------------------------------------------------
# Compare only timestamps shared by Valence and Arousal
# ---------------------------------------------------------

common_cols = [c for c in a_cols if c in set(v_cols)]

a_common = arousal[common_cols]
v_common = valence[common_cols]

print("\nCommon timestamp analysis")
print("Common timestamp columns:", len(common_cols))

print(
    "Common range:",
    timestamp_ms(common_cols[0]) / 1000,
    "to",
    timestamp_ms(common_cols[-1]) / 1000,
    "seconds"
)

a_nan = a_common.isna().to_numpy()
v_nan = v_common.isna().to_numpy()

same_nan_mask = a_nan == v_nan

print(
    "V/A NaN masks identical on common timestamps:",
    bool(same_nan_mask.all())
)

print(
    "Different V/A NaN locations:",
    int((~same_nan_mask).sum())
)


# ---------------------------------------------------------
# Check for internal missing values
# ---------------------------------------------------------

def count_internal_gaps(row):
    valid_positions = [
        i for i, value in enumerate(row)
        if pd.notna(value)
    ]

    if not valid_positions:
        return 0

    first = valid_positions[0]
    last = valid_positions[-1]

    return int(
        row.iloc[first:last + 1].isna().sum()
    )


a_internal_gaps = a_common.apply(
    count_internal_gaps,
    axis=1
)

v_internal_gaps = v_common.apply(
    count_internal_gaps,
    axis=1
)

print("\nInternal-gap analysis")

print(
    "Arousal songs with internal NaN gaps:",
    int((a_internal_gaps > 0).sum())
)

print(
    "Valence songs with internal NaN gaps:",
    int((v_internal_gaps > 0).sum())
)

print(
    "Arousal total internal NaN cells:",
    int(a_internal_gaps.sum())
)

print(
    "Valence total internal NaN cells:",
    int(v_internal_gaps.sum())
)


# ---------------------------------------------------------
# First/last valid timestamp per song
# ---------------------------------------------------------

def valid_range(row):
    valid_columns = [
        column
        for column, value in row.items()
        if pd.notna(value)
    ]

    if not valid_columns:
        return None, None

    return (
        timestamp_ms(valid_columns[0]) / 1000,
        timestamp_ms(valid_columns[-1]) / 1000
    )


a_ranges = [
    valid_range(row)
    for _, row in a_common.iterrows()
]

v_ranges = [
    valid_range(row)
    for _, row in v_common.iterrows()
]

a_first = [x[0] for x in a_ranges]
a_last = [x[1] for x in a_ranges]

v_first = [x[0] for x in v_ranges]
v_last = [x[1] for x in v_ranges]

print("\nPer-song valid temporal ranges")

print(
    "Arousal first-valid timestamps:",
    min(a_first),
    "to",
    max(a_first)
)

print(
    "Valence first-valid timestamps:",
    min(v_first),
    "to",
    max(v_first)
)

print(
    "Arousal last-valid timestamps:",
    min(a_last),
    "to",
    max(a_last)
)

print(
    "Valence last-valid timestamps:",
    min(v_last),
    "to",
    max(v_last)
)

print(
    "V/A valid temporal ranges identical:",
    a_ranges == v_ranges
)


# ---------------------------------------------------------
# Sequence integrity
# ---------------------------------------------------------

expected_a = list(
    range(
        a_times[0],
        a_times[-1] + 500,
        500
    )
)

expected_v = list(
    range(
        v_times[0],
        v_times[-1] + 500,
        500
    )
)

print("\nSequence integrity")

print(
    "Arousal exact 500 ms sequence:",
    a_times == expected_a
)

print(
    "Valence exact 500 ms sequence:",
    v_times == expected_v
)

print("\nRESULT:")
print(
    "Global CSV widths differ by one timestamp column. "
    "Paired V/A integrity must therefore be evaluated "
    "using shared valid timestamps per song."
)

# ---------------------------------------------------------
# Identify exact V/A availability mismatches
# ---------------------------------------------------------

print("\n===== V/A AVAILABILITY MISMATCH DETAILS =====")

mismatch_count = 0

print("\n===== V/A AVAILABILITY MISMATCH DETAILS =====")

a_nan_df = a_common.isna()
v_nan_df = v_common.isna()

mismatch_df = a_nan_df != v_nan_df

rows, cols = mismatch_df.to_numpy().nonzero()

for row_idx, col_idx in zip(rows, cols):
    song_id = int(arousal.iloc[row_idx]["song_id"])
    column = common_cols[col_idx]

    a_missing = a_nan_df.iloc[row_idx, col_idx]
    v_missing = v_nan_df.iloc[row_idx, col_idx]

    print(
        f"Song {song_id} | "
        f"{column} | "
        f"Arousal={'NaN' if a_missing else 'VALID'} | "
        f"Valence={'NaN' if v_missing else 'VALID'}"
    )

print(
    "Total common-timestamp mismatches:",
    int(mismatch_df.to_numpy().sum())
)

arousal_only_cols = [
    c for c in a_cols
    if c not in set(v_cols)
]

valence_only_cols = [
    c for c in v_cols
    if c not in set(a_cols)
]

print("\nTarget-specific timestamp columns")
print("Arousal-only columns:", arousal_only_cols)
print("Valence-only columns:", valence_only_cols)

for column in arousal_only_cols:
    valid_rows = arousal.loc[
        arousal[column].notna(),
        ["song_id", column]
    ]

    print(
        f"\nValid values in Arousal-only column {column}:",
        len(valid_rows)
    )

    if not valid_rows.empty:
        print(valid_rows.to_string(index=False))

print("Total common-timestamp mismatches:", mismatch_count)


# Check Arousal-only global timestamp(s)
arousal_only_cols = [c for c in a_cols if c not in set(v_cols)]
valence_only_cols = [c for c in v_cols if c not in set(a_cols)]

print("\nTarget-specific timestamp columns")
print("Arousal-only columns:", arousal_only_cols)
print("Valence-only columns:", valence_only_cols)

for column in arousal_only_cols:
    valid_rows = arousal.loc[
        arousal[column].notna(),
        ["song_id", column]
    ]

    print(
        f"\nValid values in Arousal-only column {column}:",
        len(valid_rows)
    )

    if not valid_rows.empty:
        print(valid_rows.to_string(index=False))