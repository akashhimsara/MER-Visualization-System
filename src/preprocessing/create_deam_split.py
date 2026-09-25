from pathlib import Path
import random

import pandas as pd
import yaml


CONFIG_PATH = Path("configs/reproducibility.yaml")

AROUSAL_PATH = Path(
    "data/raw/deam/annotations/"
    "annotations averaged per song/"
    "dynamic (per second annotations)/"
    "arousal.csv"
)

OUTPUT_DIR = Path("data/splits")
OUTPUT_PATH = OUTPUT_DIR / "deam_song_split_v1.csv"


# ---------------------------------------------------------
# Load frozen configuration
# ---------------------------------------------------------

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

split_config = config["split"]

seed = int(split_config["primary_seed"])
train_ratio = float(split_config["train_ratio"])
val_ratio = float(split_config["validation_ratio"])
test_ratio = float(split_config["test_ratio"])


# ---------------------------------------------------------
# Validate ratios
# ---------------------------------------------------------

ratio_sum = train_ratio + val_ratio + test_ratio

if abs(ratio_sum - 1.0) > 1e-9:
    raise ValueError(
        f"Split ratios must sum to 1.0, got {ratio_sum}"
    )


# ---------------------------------------------------------
# Obtain canonical song IDs
# ---------------------------------------------------------

annotations = pd.read_csv(
    AROUSAL_PATH,
    usecols=["song_id"]
)

song_ids = annotations["song_id"].astype(int).tolist()

if len(song_ids) != 1802:
    raise ValueError(
        f"Expected 1802 songs, found {len(song_ids)}"
    )

if len(song_ids) != len(set(song_ids)):
    raise ValueError("Duplicate song IDs detected")


# Sort BEFORE deterministic shuffle
song_ids = sorted(song_ids)

rng = random.Random(seed)
rng.shuffle(song_ids)


# ---------------------------------------------------------
# Calculate exact split sizes
# ---------------------------------------------------------

total = len(song_ids)

train_count = int(total * train_ratio)
val_count = int(total * val_ratio)

# Remainder goes to TEST so every song is assigned exactly once.
test_count = total - train_count - val_count

train_ids = song_ids[:train_count]

val_ids = song_ids[
    train_count:
    train_count + val_count
]

test_ids = song_ids[
    train_count + val_count:
]


# ---------------------------------------------------------
# Build canonical manifest
# ---------------------------------------------------------

rows = []

for song_id in train_ids:
    rows.append(
        {
            "song_id": song_id,
            "split": "train"
        }
    )

for song_id in val_ids:
    rows.append(
        {
            "song_id": song_id,
            "split": "validation"
        }
    )

for song_id in test_ids:
    rows.append(
        {
            "song_id": song_id,
            "split": "test"
        }
    )

manifest = pd.DataFrame(rows)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

manifest.to_csv(
    OUTPUT_PATH,
    index=False
)


# ---------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------

all_assigned = (
    set(train_ids)
    | set(val_ids)
    | set(test_ids)
)

train_val_overlap = set(train_ids) & set(val_ids)
train_test_overlap = set(train_ids) & set(test_ids)
val_test_overlap = set(val_ids) & set(test_ids)


print("===== DEAM CANONICAL SONG SPLIT =====")

print("\nConfiguration")
print("Seed:", seed)
print(
    "Ratios:",
    train_ratio,
    val_ratio,
    test_ratio
)

print("\nCounts")
print("Total:", total)
print("Train:", len(train_ids))
print("Validation:", len(val_ids))
print("Test:", len(test_ids))

print("\nLeakage checks")
print(
    "Train/Validation overlap:",
    len(train_val_overlap)
)
print(
    "Train/Test overlap:",
    len(train_test_overlap)
)
print(
    "Validation/Test overlap:",
    len(val_test_overlap)
)

print(
    "Unique assigned songs:",
    len(all_assigned)
)

print(
    "All source songs assigned:",
    all_assigned == set(song_ids)
)

print("\nManifest:")
print(OUTPUT_PATH)

if (
    len(manifest) == 1802
    and len(all_assigned) == 1802
    and not train_val_overlap
    and not train_test_overlap
    and not val_test_overlap
):
    print(
        "\nRESULT: PASS - canonical song-level "
        "split created without leakage"
    )
else:
    print("\nRESULT: REVIEW REQUIRED")