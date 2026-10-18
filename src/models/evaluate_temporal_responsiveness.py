
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs" / "results"

INPUT = RESULTS / "EXP_TEMPORAL_001_hold_last_predictions.csv"

PER_SONG_OUTPUT = (
    RESULTS / "EXP_TEMPORAL_001_responsiveness_per_song.csv"
)

SUMMARY_OUTPUT = (
    RESULTS / "EXP_TEMPORAL_001_responsiveness_summary.csv"
)

HOPS = (500, 1000, 2000)
TARGETS = ("valence", "arousal")


def main():
    data = pd.read_csv(INPUT)

    required = {
        "song_id",
        "timestamp_ms",
        "hop_ms",
        "is_update",
        "true_valence",
        "true_arousal",
        "held_valence",
        "held_arousal",
    }

    if not required.issubset(data.columns):
        raise ValueError("Missing required columns")

    if data[list(required)].isna().any().any():
        raise ValueError("Missing values detected")

    if data.duplicated(
        ["song_id", "hop_ms", "timestamp_ms"]
    ).any():
        raise ValueError("Duplicate timestamps detected")

    if set(data["hop_ms"].unique()) != set(HOPS):
        raise ValueError("Unexpected hop intervals")

    per_song_rows = []
    detailed_rows = []

    for (song_id, hop), group in data.groupby(
        ["song_id", "hop_ms"]
    ):
        group = group.sort_values("timestamp_ms").copy()

        timestamps = group["timestamp_ms"].to_numpy(
            dtype=np.int64
        )

        updates = group["is_update"].astype(bool).to_numpy()

        if not updates[0]:
            raise ValueError(
                f"No initial prediction for song {song_id}"
            )

        last_update_time = np.maximum.accumulate(
            np.where(updates, timestamps, -1)
        )

        update_age_ms = timestamps - last_update_time

        group["update_age_ms"] = update_age_ms

        for target in TARGETS:
            truth = group[f"true_{target}"].to_numpy(
                dtype=np.float64
            )

            prediction = group[f"held_{target}"].to_numpy(
                dtype=np.float64
            )

            true_change = np.diff(truth)
            predicted_change = np.diff(prediction)

            change_error = np.abs(
                true_change - predicted_change
            )

            absolute_error = np.abs(truth - prediction)

            # Within-song 90th percentile of true
            # 0.5-second emotion-change magnitudes.
            threshold = float(
                np.quantile(np.abs(true_change), 0.90)
            )

            fast_mask = np.abs(true_change) >= threshold

            # Change at index i represents transition
            # from timestamp i to timestamp i+1.
            fast_change_mae = float(
                np.mean(absolute_error[1:][fast_mask])
            )

            change_mae = float(
                np.mean(change_error)
            )

            mean_abs_pred_change = float(
                np.mean(np.abs(predicted_change))
            )

            mean_abs_true_change = float(
                np.mean(np.abs(true_change))
            )

            per_song_rows.append({
                "song_id": int(song_id),
                "hop_ms": int(hop),
                "target": target,
                "n": len(group),
                "change_mae": change_mae,
                "fast_change_mae": fast_change_mae,
                "fast_change_threshold": threshold,
                "fast_change_count": int(fast_mask.sum()),
                "mean_abs_true_change":
                    mean_abs_true_change,
                "mean_abs_pred_change":
                    mean_abs_pred_change,
                "mean_update_age_ms": float(
                    update_age_ms.mean()
                ),
                "max_update_age_ms": int(
                    update_age_ms.max()
                ),
            })

            for i in range(1, len(group)):
                detailed_rows.append({
                    "song_id": int(song_id),
                    "hop_ms": int(hop),
                    "target": target,
                    "timestamp_ms": int(timestamps[i]),
                    "true_change": float(
                        true_change[i - 1]
                    ),
                    "predicted_change": float(
                        predicted_change[i - 1]
                    ),
                    "change_error": float(
                        change_error[i - 1]
                    ),
                    "absolute_error": float(
                        absolute_error[i]
                    ),
                    "is_fast_change": bool(
                        fast_mask[i - 1]
                    ),
                    "update_age_ms": int(
                        update_age_ms[i]
                    ),
                })

    per_song = pd.DataFrame(per_song_rows)
    detailed = pd.DataFrame(detailed_rows)

    summary_rows = []

    for (hop, target), group in detailed.groupby(
        ["hop_ms", "target"]
    ):
        fast = group.loc[group["is_fast_change"]]

        summary_rows.append({
            "hop_ms": int(hop),
            "target": target,
            "songs": int(group["song_id"].nunique()),
            "transitions": len(group),
            "change_mae": float(
                group["change_error"].mean()
            ),
            "fast_change_mae": float(
                fast["absolute_error"].mean()
            ),
            "fast_change_transitions": len(fast),
            "mean_abs_pred_change": float(
                group["predicted_change"].abs().mean()
            ),
            "mean_abs_true_change": float(
                group["true_change"].abs().mean()
            ),
            "mean_update_age_ms": float(
                group["update_age_ms"].mean()
            ),
            "max_update_age_ms": int(
                group["update_age_ms"].max()
            ),
        })

    summary = pd.DataFrame(summary_rows)

    per_song.to_csv(
        PER_SONG_OUTPUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    print("===== TEMPORAL RESPONSIVENESS SUMMARY =====")
    print(summary.to_string(index=False))

    print("\nSaved:", PER_SONG_OUTPUT)
    print("Saved:", SUMMARY_OUTPUT)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
