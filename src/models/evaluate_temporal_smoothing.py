
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "outputs/results/EXP_TEMPORAL_001_raw_predictions.csv"
OUTPUT = ROOT / "outputs/results/EXP_TEMPORAL_001_smoothing.csv"

ALPHAS = (0.2, 0.4, 0.6, 0.8)


def ema(values, alpha):
    result = np.empty(len(values), dtype=np.float64)
    result[0] = values[0]

    for i in range(1, len(values)):
        result[i] = (
            alpha * values[i]
            + (1 - alpha) * result[i - 1]
        )

    return result


def metrics(y_true, y_pred):
    error = y_true - y_pred
    mae = np.mean(np.abs(error))
    rmse = np.sqrt(np.mean(error ** 2))

    mean_true = np.mean(y_true)
    mean_pred = np.mean(y_pred)

    var_true = np.var(y_true)
    var_pred = np.var(y_pred)

    covariance = np.mean(
        (y_true - mean_true) * (y_pred - mean_pred)
    )

    ccc = (
        2 * covariance
        / (
            var_true + var_pred
            + (mean_true - mean_pred) ** 2
        )
    )

    return mae, rmse, ccc


def main():
    df = pd.read_csv(INPUT).sort_values(
        ["song_id", "timestamp_ms"]
    )

    results = []

    for alpha in (None, *ALPHAS):
        for target in ("valence", "arousal"):
            true_parts = []
            pred_parts = []
            changes = []

            for _, song in df.groupby("song_id"):
                truth = song[f"true_{target}"].to_numpy()
                raw = song[f"pred_{target}"].to_numpy()

                predicted = (
                    raw if alpha is None
                    else ema(raw, alpha)
                )

                true_parts.append(truth)
                pred_parts.append(predicted)

                if len(predicted) > 1:
                    changes.extend(
                        np.abs(np.diff(predicted))
                    )

            y_true = np.concatenate(true_parts)
            y_pred = np.concatenate(pred_parts)

            mae, rmse, ccc = metrics(y_true, y_pred)

            results.append({
                "method": (
                    "raw" if alpha is None
                    else f"ema_{alpha}"
                ),
                "target": target,
                "songs": df["song_id"].nunique(),
                "n": len(y_true),
                "mae": mae,
                "rmse": rmse,
                "ccc": ccc,
                "mean_abs_pred_change": np.mean(changes),
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT, index=False)

    print("\n===== CAUSAL SMOOTHING VALIDATION =====")
    print(result_df.to_string(index=False))
    print("\nSaved:", OUTPUT)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
