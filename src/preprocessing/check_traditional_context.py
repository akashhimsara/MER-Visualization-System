from pathlib import Path

import librosa
import pandas as pd
import yaml


CONFIG_PATH = Path("configs/traditional_baseline_v1.yaml")
TARGET_PATH = Path("data/processed/deam_paired_va_targets_v1.csv")
AUDIO_DIR = Path("data/raw/deam/MEMD_audio")


# ---------------------------------------------------------
# Load configuration
# ---------------------------------------------------------

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

context_seconds = float(
    config["temporal"]["context_seconds"]
)


# ---------------------------------------------------------
# Load canonical targets
# ---------------------------------------------------------

targets = pd.read_csv(TARGET_PATH)

violations = []
checked = 0

min_context_start = float("inf")
max_context_end = float("-inf")
min_audio_margin = float("inf")


print("===== TRADITIONAL CONTEXT BOUNDARY CHECK =====")

for song_id, group in targets.groupby("song_id"):

    audio_path = AUDIO_DIR / f"{song_id}.mp3"

    duration = librosa.get_duration(
        path=audio_path
    )

    for timestamp in group["timestamp_sec"]:

        timestamp = float(timestamp)

        context_start = timestamp - context_seconds
        context_end = timestamp

        min_context_start = min(
            min_context_start,
            context_start
        )

        max_context_end = max(
            max_context_end,
            context_end
        )

        audio_margin = duration - context_end

        min_audio_margin = min(
            min_audio_margin,
            audio_margin
        )

        if context_start < 0:
            violations.append(
                (
                    int(song_id),
                    timestamp,
                    "context starts before audio"
                )
            )

        if context_end > duration:
            violations.append(
                (
                    int(song_id),
                    timestamp,
                    "context ends after audio"
                )
            )

        checked += 1


print("\nConfiguration")
print("Context seconds:", context_seconds)
print("Alignment: causal [t-context, t]")

print("\nSamples")
print("Target contexts checked:", checked)

print("\nBoundary statistics")
print(
    "Earliest context start:",
    f"{min_context_start:.3f} s"
)
print(
    "Latest context end:",
    f"{max_context_end:.3f} s"
)
print(
    "Smallest audio-end margin:",
    f"{min_audio_margin:.3f} s"
)

print("\nViolations:", len(violations))

if violations:
    print("\nFirst violations:")

    for item in violations[:20]:
        print(item)

    print("\nRESULT: REVIEW REQUIRED")

else:
    print(
        "\nRESULT: PASS - all canonical targets "
        "support the frozen 5-second causal context"
    )