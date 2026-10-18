
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    ROOT / "outputs/results/"
    "EXP_TEMPORAL_001_raw_predictions.csv"
)

OUTPUT_DIR = ROOT / "outputs/results"

HOPS_MS = (500, 1000, 2000)
TARGETS = ("valence", "arousal")


def ccc(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    my = y.mean()
    mp = p.mean()

    vy = y.var()
    vp = p.var()

    cov = np.mean((y - my) * (p - mp))

    denominator = vy + vp + (my - mp) ** 2

    if denominator <= 0:
        return np.nan

    return float(2 * cov / denominator)


def calculate_metrics(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    pearson = (
        float(np.corrcoef(y, p)[0, 1])
        if len(y) > 1 and y.std() > 0 and p.std() > 0
        else np.nan
    )

    return {
        "mae": float(np.mean(np.abs(y - p))),
        "rmse": float(np.sqrt(np.mean((y - p) ** 2))),
        "pearson": pearson,
        "ccc": ccc(y, p),
        "mean_abs_pred_change": (
            float(np.mean(np.abs(np.diff(p))))
            if len(p) > 1 else np.nan
        ),
    }


def main():
    print("===== CAUSAL HOLD-LAST HOP EVALUATION =====")
    print("TEST: LOCKED / NOT EVALUATED")

    data = pd.read_csv(INPUT_PATH)

    required = {
        "song_id",
        "timestamp_ms",
        "true_valence",
        "true_arousal",
        "pred_valence",
        "pred_arousal",
    }

    if not required.issubset(data.columns):
        raise ValueError("Missing required columns")

    if data.isna().any().any():
        raise ValueError("Missing values detected")

    if data.duplicated(
        ["song_id", "timestamp_ms"]
    ).any():
        raise ValueError("Duplicate song timestamps")

    data = data.sort_values(
        ["song_id", "timestamp_ms"]
    ).reset_index(drop=True)

    predictions = []
    per_song_rows = []
    aggregate_rows = []

    for hop_ms in HOPS_MS:
        for song_id, group in data.groupby("song_id"):
            group = group.sort_values(
                "timestamp_ms"
            ).copy()

            timestamps = group[
                "timestamp_ms"
            ].to_numpy(dtype=np.int64)

            if timestamps[0] != 15000:
                raise ValueError(
                    f"Unexpected first timestamp: {song_id}"
                )

            if not np.all(
                np.diff(timestamps) == 500
            ):
                raise ValueError(
                    f"Unexpected timestamp spacing: {song_id}"
                )

            # Update only at allowed causal timestamps.
            update_mask = (
                (timestamps - 15000) % hop_ms == 0
            )

            group["hop_ms"] = hop_ms
            group["is_update"] = update_mask

            for target in TARGETS:
                raw = group[
                    f"pred_{target}"
                ].to_numpy(dtype=np.float64)

                held = np.empty_like(raw)
                last_prediction = None

                for i in range(len(raw)):
                    if update_mask[i]:
                        last_prediction = raw[i]

                    if last_prediction is None:
                        raise ValueError(
                            "Prediction unavailable before update"
                        )

                    held[i] = last_prediction

                group[f"held_{target}"] = held

                truth = group[
                    f"true_{target}"
                ].to_numpy(dtype=np.float64)

                metrics = calculate_metrics(
                    truth,
                    held,
                )

                per_song_rows.append({
                    "song_id": int(song_id),
                    "hop_ms": hop_ms,
                    "target": target,
                    "n": len(group),
                    "updates": int(update_mask.sum()),
                    **metrics,
                })

            predictions.append(group)

        # Aggregate using identical canonical timestamps.
        hop_predictions = pd.concat(
            [
                frame
                for frame in predictions
                if frame["hop_ms"].iloc[0] == hop_ms
            ],
            ignore_index=True,
        )

        for target in TARGETS:
            truth = hop_predictions[
                f"true_{target}"
            ].to_numpy(dtype=np.float64)

            held = hop_predictions[
                f"held_{target}"
            ].to_numpy(dtype=np.float64)

            metrics = calculate_metrics(
                truth,
                held,
            )

            aggregate_rows.append({
                "hop_ms": hop_ms,
                "target": target,
                "songs": hop_predictions["song_id"].nunique(),
                "n": len(hop_predictions),
                "updates": int(
                    hop_predictions["is_update"].sum()
                ),
                **metrics,
            })

    prediction_df = pd.concat(
        predictions,
        ignore_index=True,
    )

    per_song_df = pd.DataFrame(
        per_song_rows
    )

    aggregate_df = pd.DataFrame(
        aggregate_rows
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    prediction_path = (
        OUTPUT_DIR /
        "EXP_TEMPORAL_001_hold_last_predictions.csv"
    )

    per_song_path = (
        OUTPUT_DIR /
        "EXP_TEMPORAL_001_hold_last_per_song.csv"
    )

    aggregate_path = (
        OUTPUT_DIR /
        "EXP_TEMPORAL_001_hold_last_aggregate.csv"
    )

    prediction_df.to_csv(
        prediction_path,
        index=False,
    )

    per_song_df.to_csv(
        per_song_path,
        index=False,
    )

    aggregate_df.to_csv(
        aggregate_path,
        index=False,
    )

    print("\n===== AGGREGATE RESULTS =====")
    print(
        aggregate_df.to_string(index=False)
    )

    print("\nSaved:", prediction_path)
    print("Saved:", per_song_path)
    print("Saved:", aggregate_path)

    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
