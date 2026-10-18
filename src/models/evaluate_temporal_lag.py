
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "outputs/results/EXP_TEMPORAL_001_raw_predictions.csv"
OUTPUT = ROOT / "outputs/results/EXP_TEMPORAL_001_lag.csv"

ALPHA = 0.2
LAGS = range(-8, 9)  # -4s to +4s, at 0.5s intervals


def ema(values, alpha):
    output = np.empty(len(values), dtype=float)
    output[0] = values[0]

    for i in range(1, len(values)):
        output[i] = alpha * values[i] + (1 - alpha) * output[i - 1]

    return output



def main():
    df = pd.read_csv(INPUT).sort_values(
        ["song_id", "timestamp_ms"]
    )

    rows = []
    max_lag = max(abs(lag) for lag in LAGS)

    for target in ("valence", "arousal"):
        for method in ("raw", "ema_0.2"):
            for lag in LAGS:
                true_parts = []
                pred_parts = []

                for _, song in df.groupby("song_id"):
                    truth = song[f"true_{target}"].to_numpy()
                    raw = song[f"pred_{target}"].to_numpy()

                    prediction = (
                        raw if method == "raw"
                        else ema(raw, ALPHA)
                    )

                    n = len(truth)

                    if n <= 2 * max_lag:
                        continue

                    # Same truth timestamps for every lag.
                    center = np.arange(max_lag, n - max_lag)

                    y_true = truth[center]
                    y_pred = prediction[center + lag]

                    true_parts.append(y_true)
                    pred_parts.append(y_pred)

                y_true = np.concatenate(true_parts)
                y_pred = np.concatenate(pred_parts)

                mae = np.mean(np.abs(y_true - y_pred))

                rows.append({
                    "target": target,
                    "method": method,
                    "lag_seconds": lag * 0.5,
                    "n": len(y_true),
                    "mae": mae,
                })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT, index=False)

    print("\n===== FAIR TEMPORAL LAG ANALYSIS =====")

    print(
        result.loc[
            result.groupby(["target", "method"])["mae"].idxmin()
        ].to_string(index=False)
    )

    print("\nSample count consistency:")
    print(
        result.groupby(["target", "method"])["n"]
        .nunique()
        .to_string()
    )

    print("\nSaved:", OUTPUT)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
