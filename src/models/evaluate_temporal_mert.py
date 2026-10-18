
from pathlib import Path
import argparse

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


ROOT = Path(__file__).resolve().parents[2]

CHUNK_DIR = ROOT / "outputs/embeddings/EXP_MERT_001/chunks"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"
SPLIT_FILE = ROOT / "data/splits/deam_song_split_v1.csv"
TARGET_FILE = ROOT / "data/processed/deam_paired_va_targets_v1.csv"
OUTPUT_DIR = ROOT / "outputs/results"

HOPS_MS = (500, 1000, 2000)


def ccc(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    my, mp = y.mean(), p.mean()
    vy, vp = y.var(), p.var()
    cov = np.mean((y - my) * (p - mp))

    denom = vy + vp + (my - mp) ** 2

    return float(2 * cov / denom) if denom > 0 else np.nan


def metrics(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    pearson = (
        float(np.corrcoef(y, p)[0, 1])
        if len(y) >= 2 and y.std() > 0 and p.std() > 0
        else np.nan
    )

    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(np.sqrt(mean_squared_error(y, p))),
        "pearson": pearson,
        "ccc": ccc(y, p),
        "r2": float(r2_score(y, p)) if len(y) >= 2 else np.nan,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-songs", type=int, default=270)
    args = parser.parse_args()

    if not 1 <= args.max_songs <= 270:
        raise ValueError("--max-songs must be between 1 and 270")

    splits = pd.read_csv(SPLIT_FILE)
    targets = pd.read_csv(TARGET_FILE)

    validation_ids = sorted(
        splits.loc[splits["split"] == "validation", "song_id"]
        .astype(int)
        .tolist()
    )

    assert len(validation_ids) == 270

    selected_ids = validation_ids[:args.max_songs]

    v_scaler = joblib.load(MODEL_DIR / "layer_4/scaler.joblib")
    v_model = joblib.load(MODEL_DIR / "layer_4/valence_ridge.joblib")
    a_scaler = joblib.load(MODEL_DIR / "layer_8/scaler.joblib")
    a_model = joblib.load(MODEL_DIR / "layer_8/arousal_ridge.joblib")

    all_predictions = []

    for song_id in selected_ids:
        path = CHUNK_DIR / f"song_{song_id:04d}.npz"

        if not path.is_file():
            raise FileNotFoundError(path)

        with np.load(path, allow_pickle=False) as chunk:
            if not np.all(chunk["split"] == "validation"):
                raise ValueError(f"Non-validation chunk: {song_id}")

            if not np.all(chunk["song_id"] == song_id):
                raise ValueError(f"Song mismatch: {song_id}")

            times = chunk["timestamp_ms"].astype(np.int64)
            v_true = chunk["valence"].astype(np.float64)
            a_true = chunk["arousal"].astype(np.float64)

            v_pred = v_model.predict(
                v_scaler.transform(chunk["layer_4"])
            )
            a_pred = a_model.predict(
                a_scaler.transform(chunk["layer_8"])
            )

        if not np.isfinite(v_pred).all() or not np.isfinite(a_pred).all():
            raise ValueError(f"Non-finite predictions: {song_id}")

        for i, timestamp in enumerate(times):
            all_predictions.append({
                "song_id": song_id,
                "timestamp_ms": int(timestamp),
                "true_valence": float(v_true[i]),
                "true_arousal": float(a_true[i]),
                "pred_valence": float(v_pred[i]),
                "pred_arousal": float(a_pred[i]),
            })

    predictions = pd.DataFrame(all_predictions)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    predictions = predictions.sort_values(
        ["song_id", "timestamp_ms"]
        ).reset_index(drop=True)

    prediction_path = (
        OUTPUT_DIR / "EXP_TEMPORAL_001_raw_predictions.csv"
        )

    predictions.to_csv(prediction_path, index=False)

    print("Raw predictions saved:", prediction_path)

    # Verify alignment against canonical ground-truth manifest.
    reference = targets.loc[
        (targets["split"] == "validation")
        & (targets["song_id"].isin(selected_ids)),
        ["song_id", "timestamp_ms", "valence", "arousal"],
    ]

    aligned = predictions.merge(
        reference,
        on=["song_id", "timestamp_ms"],
        how="inner",
        validate="one_to_one",
    )

    if len(aligned) != len(predictions) or len(aligned) != len(reference):
        raise ValueError("Canonical timestamp alignment failed")

    if not np.allclose(
        aligned["true_valence"], aligned["valence"], atol=1e-6
    ):
        raise ValueError("Valence label mismatch")

    if not np.allclose(
        aligned["true_arousal"], aligned["arousal"], atol=1e-6
    ):
        raise ValueError("Arousal label mismatch")

    per_song = []
    aggregate = []

    # All hops use the same 15-second origin.
    for hop_ms in HOPS_MS:
        subset = aligned.loc[
            (aligned["timestamp_ms"] - 15000) % hop_ms == 0
        ].copy()

        for song_id, group in subset.groupby("song_id"):
            group = group.sort_values("timestamp_ms")

            for target in ("valence", "arousal"):
                y = group[f"true_{target}"].to_numpy()
                p = group[f"pred_{target}"].to_numpy()

                result = metrics(y, p)

                per_song.append({
                    "song_id": int(song_id),
                    "hop_ms": hop_ms,
                    "target": target,
                    "n": len(group),
                    **result,
                    "mean_abs_pred_change": float(
                        np.mean(np.abs(np.diff(p)))
                    ) if len(p) > 1 else np.nan,
                    "mean_abs_truth_change": float(
                        np.mean(np.abs(np.diff(y)))
                    ) if len(y) > 1 else np.nan,
                })

        for target in ("valence", "arousal"):
            y = subset[f"true_{target}"].to_numpy()
            p = subset[f"pred_{target}"].to_numpy()

            aggregate.append({
                "hop_ms": hop_ms,
                "target": target,
                "songs": subset["song_id"].nunique(),
                "n": len(subset),
                **metrics(y, p),
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    per_song_path = OUTPUT_DIR / "EXP_TEMPORAL_001_per_song.csv"
    aggregate_path = OUTPUT_DIR / "EXP_TEMPORAL_001_aggregate.csv"

    pd.DataFrame(per_song).to_csv(per_song_path, index=False)
    pd.DataFrame(aggregate).to_csv(aggregate_path, index=False)

    print("\n===== TEMPORAL VALIDATION =====")
    print(pd.DataFrame(aggregate).to_string(index=False))
    print("\nSaved:", per_song_path)
    print("Saved:", aggregate_path)
    print("Validation songs:", len(selected_ids))
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
