
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs" / "results"

INPUT = RESULTS / "EXP_TEMPORAL_001_hold_last_per_song.csv"

OUTPUT = (
    RESULTS / "EXP_TEMPORAL_001_hop_bootstrap.csv"
)

SEED = 42
BOOTSTRAP_SAMPLES = 10000

# Compare 1-second candidate against alternatives.
COMPARISONS = [
    (500, 1000),
    (2000, 1000),
]

TARGETS = ["valence", "arousal"]
METRICS = ["mae", "rmse", "ccc"]


def paired_bootstrap(values_a, values_b, rng):
    """
    Difference = B - A.

    For MAE/RMSE:
        Negative means B is better.

    For CCC:
        Positive means B is better.

    Songs are resampled as paired units.
    """
    differences = values_b - values_a

    n = len(differences)

    bootstrap_means = np.empty(
        BOOTSTRAP_SAMPLES,
        dtype=np.float64,
    )

    for i in range(BOOTSTRAP_SAMPLES):
        indices = rng.integers(
            0,
            n,
            size=n,
        )

        bootstrap_means[i] = (
            differences[indices].mean()
        )

    lower, upper = np.percentile(
        bootstrap_means,
        [2.5, 97.5],
    )

    return {
        "mean_difference_B_minus_A": float(
            differences.mean()
        ),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "songs_B_better": int(
            np.sum(
                differences < 0
            )
        ),
        "songs_A_better": int(
            np.sum(
                differences > 0
            )
        ),
        "songs_equal": int(
            np.sum(
                differences == 0
            )
        ),
    }


def main():
    data = pd.read_csv(INPUT)

    required = {
        "song_id",
        "hop_ms",
        "target",
        *METRICS,
    }

    if not required.issubset(data.columns):
        raise ValueError(
            "Missing required columns"
        )

    if data.duplicated(
        ["song_id", "hop_ms", "target"]
    ).any():
        raise ValueError(
            "Duplicate song/hop/target rows"
        )

    if data[list(required)].isna().any().any():
        raise ValueError(
            "Missing values detected"
        )

    if data["song_id"].nunique() != 270:
        raise ValueError(
            "Expected 270 validation songs"
        )

    rng = np.random.default_rng(SEED)
    rows = []

    for target in TARGETS:
        subset = data.loc[
            data["target"] == target
        ]

        for metric in METRICS:
            pivot = subset.pivot(
                index="song_id",
                columns="hop_ms",
                values=metric,
            ).sort_index()

            if set(pivot.columns) != {
                500, 1000, 2000
            }:
                raise ValueError(
                    "Unexpected hop values"
                )

            for hop_a, hop_b in COMPARISONS:
                values_a = pivot[
                    hop_a
                ].to_numpy(
                    dtype=np.float64
                )

                values_b = pivot[
                    hop_b
                ].to_numpy(
                    dtype=np.float64
                )

                result = paired_bootstrap(
                    values_a,
                    values_b,
                    rng,
                )

                # CCC is higher-is-better.
                # MAE and RMSE are lower-is-better.
                if metric == "ccc":
                    result["songs_B_better"] = int(
                        np.sum(values_b > values_a)
                    )
                    result["songs_A_better"] = int(
                        np.sum(values_b < values_a)
                    )

                rows.append({
                    "target": target,
                    "metric": metric,
                    "hop_A_ms": hop_a,
                    "hop_B_ms": hop_b,
                    "songs": len(pivot),
                    **result,
                    "ci_excludes_zero": bool(
                        result["ci95_lower"] > 0
                        or result["ci95_upper"] < 0
                    ),
                })

    output = pd.DataFrame(rows)

    output.to_csv(
        OUTPUT,
        index=False,
    )

    print(
        "===== PAIRED SONG-LEVEL BOOTSTRAP ====="
    )

    print(
        output.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print("\nSaved:", OUTPUT)
    print("Bootstrap samples:", BOOTSTRAP_SAMPLES)
    print("Seed:", SEED)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
