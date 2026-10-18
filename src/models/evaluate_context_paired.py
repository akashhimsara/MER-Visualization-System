
from pathlib import Path
import argparse

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

SPLIT_FILE = ROOT / "data/splits/deam_song_split_v1.csv"
TARGET_FILE = ROOT / "data/processed/deam_paired_va_targets_v1.csv"
OUTPUT_DIR = ROOT / "outputs/results"

CONTEXTS = {
    3: {
        "embeddings": ROOT / "outputs/embeddings/EXP_CONTEXT_3S/chunks",
        "models": ROOT / "outputs/models/EXP_CONTEXT_3S",
        "valence_layer": 4,
        "arousal_layer": 8,
    },
    5: {
        "embeddings": ROOT / "outputs/embeddings/EXP_MERT_001/chunks",
        "models": ROOT / "outputs/models/EXP_MERT_001",
        "valence_layer": 4,
        "arousal_layer": 8,
    },
    8: {
        "embeddings": ROOT / "outputs/embeddings/EXP_CONTEXT_8S/chunks",
        "models": ROOT / "outputs/models/EXP_CONTEXT_8S",
        "valence_layer": 8,
        "arousal_layer": 8,
    },
}

TARGETS = ("valence", "arousal")
BOOTSTRAP_REPS = 10000
SEED = 42


def load_models(config):
    models = {}

    for target in TARGETS:
        layer = config[f"{target}_layer"]
        folder = config["models"] / f"layer_{layer}"

        scaler = joblib.load(folder / "scaler.joblib")
        ridge = joblib.load(folder / f"{target}_ridge.joblib")

        models[target] = (layer, scaler, ridge)

    return models


def load_song_predictions(song_id, context, config, models):
    path = config["embeddings"] / f"song_{song_id:04d}.npz"

    if not path.is_file():
        raise FileNotFoundError(path)

    with np.load(path, allow_pickle=False) as chunk:
        ids = np.asarray(chunk["song_id"]).astype(int)
        splits = np.asarray(chunk["split"]).astype(str)
        timestamps = np.asarray(chunk["timestamp_ms"]).astype(np.int64)

        if not np.all(ids == song_id):
            raise ValueError(f"Song ID mismatch: {path}")

        if not np.all(splits == "validation"):
            raise ValueError(f"Non-validation data: {path}")

        if len(timestamps) != len(np.unique(timestamps)):
            raise ValueError(f"Duplicate timestamps: {path}")

        result = pd.DataFrame({
            "song_id": song_id,
            "timestamp_ms": timestamps,
            "context_seconds": context,
            "true_valence": chunk["valence"].astype(np.float64),
            "true_arousal": chunk["arousal"].astype(np.float64),
        })

        for target in TARGETS:
            layer, scaler, ridge = models[target]
            features = np.asarray(chunk[f"layer_{layer}"])

            predictions = ridge.predict(scaler.transform(features))
            predictions = np.asarray(predictions, dtype=np.float64)

            if not np.isfinite(predictions).all():
                raise ValueError(
                    f"Non-finite {target} predictions: "
                    f"song={song_id}, context={context}"
                )

            result[f"pred_{target}"] = predictions

    return result


def bootstrap_paired_song_mae(
    per_song,
    context_a,
    context_b,
    target,
    rng,
):
    subset = per_song.loc[
        per_song["target"] == target,
        ["song_id", "context_seconds", "mae"],
    ]

    pivot = subset.pivot(
        index="song_id",
        columns="context_seconds",
        values="mae",
    )

    if pivot[[context_a, context_b]].isna().any().any():
        raise ValueError("Missing paired song results")

    # Positive delta means context B has lower MAE (better).
    delta = (
        pivot[context_a].to_numpy()
        - pivot[context_b].to_numpy()
    )

    n = len(delta)

    bootstrap_means = np.empty(
        BOOTSTRAP_REPS,
        dtype=np.float64,
    )

    for i in range(BOOTSTRAP_REPS):
        indices = rng.integers(0, n, size=n)
        bootstrap_means[i] = delta[indices].mean()

    ci_low, ci_high = np.percentile(
        bootstrap_means,
        [2.5, 97.5],
    )

    return {
        "target": target,
        "context_a": context_a,
        "context_b": context_b,
        "songs": n,
        "mean_mae_improvement_b_over_a": float(delta.mean()),
        "median_mae_improvement_b_over_a": float(np.median(delta)),
        "songs_b_better": int(np.sum(delta > 0)),
        "songs_a_better": int(np.sum(delta < 0)),
        "songs_tied": int(np.sum(delta == 0)),
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "bootstrap_reps": BOOTSTRAP_REPS,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-songs",
        type=int,
        default=270,
    )
    args = parser.parse_args()

    if not 1 <= args.max_songs <= 270:
        raise ValueError("--max-songs must be between 1 and 270")

    print("===== CONTEXT PAIRED VALIDATION =====")
    print("Contexts: 3s, 5s, 8s")
    print("TEST: LOCKED / NOT EVALUATED")

    splits = pd.read_csv(SPLIT_FILE)
    targets = pd.read_csv(TARGET_FILE)

    validation_ids = sorted(
        splits.loc[
            splits["split"] == "validation",
            "song_id",
        ].astype(int).tolist()
    )

    if len(validation_ids) != 270:
        raise ValueError("Expected exactly 270 validation songs")

    selected_ids = validation_ids[:args.max_songs]

    reference = targets.loc[
        (targets["split"] == "validation")
        & (targets["song_id"].isin(selected_ids)),
        ["song_id", "timestamp_ms", "valence", "arousal"],
    ].copy()

    if reference.duplicated(
        ["song_id", "timestamp_ms"]
    ).any():
        raise ValueError("Duplicate canonical labels")

    loaded_models = {
        context: load_models(config)
        for context, config in CONTEXTS.items()
    }

    all_predictions = []

    for index, song_id in enumerate(selected_ids, start=1):
        song_frames = []

        for context, config in CONTEXTS.items():
            frame = load_song_predictions(
                song_id,
                context,
                config,
                loaded_models[context],
            )

            song_frames.append(frame)

        # Require identical timestamps and ground-truth labels
        # across all three contexts.
        baseline = song_frames[1].sort_values(
            "timestamp_ms"
        ).reset_index(drop=True)

        for frame in song_frames:
            current = frame.sort_values(
                "timestamp_ms"
            ).reset_index(drop=True)

            if not np.array_equal(
                current["timestamp_ms"].to_numpy(),
                baseline["timestamp_ms"].to_numpy(),
            ):
                raise ValueError(
                    f"Timestamp mismatch for song {song_id}"
                )

            for target in TARGETS:
                if not np.allclose(
                    current[f"true_{target}"],
                    baseline[f"true_{target}"],
                    atol=1e-6,
                    rtol=0,
                ):
                    raise ValueError(
                        f"Label mismatch: song={song_id}, "
                        f"target={target}"
                    )

        all_predictions.extend(song_frames)

        if index % 50 == 0 or index == len(selected_ids):
            print(f"Processed {index}/{len(selected_ids)} songs")

    predictions = pd.concat(
        all_predictions,
        ignore_index=True,
    )

    # Verify every prediction against the canonical label file.
    aligned = predictions.merge(
        reference,
        on=["song_id", "timestamp_ms"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    if not (aligned["_merge"] == "both").all():
        raise ValueError("Missing canonical timestamps")

    expected_rows = len(reference) * len(CONTEXTS)

    if len(aligned) != expected_rows:
        raise ValueError(
            f"Row count mismatch: {len(aligned)} != {expected_rows}"
        )

    for target in TARGETS:
        if not np.allclose(
            aligned[f"true_{target}"],
            aligned[target],
            atol=1e-6,
            rtol=0,
        ):
            raise ValueError(
                f"Canonical {target} label mismatch"
            )

    per_song_rows = []
    aggregate_rows = []

    for context, context_frame in predictions.groupby(
        "context_seconds"
    ):
        for target in TARGETS:
            truth = context_frame[f"true_{target}"].to_numpy()
            pred = context_frame[f"pred_{target}"].to_numpy()

            aggregate_rows.append({
                "context_seconds": int(context),
                "target": target,
                "songs": context_frame["song_id"].nunique(),
                "n": len(context_frame),
                "mae": float(np.mean(np.abs(truth - pred))),
                "rmse": float(
                    np.sqrt(np.mean((truth - pred) ** 2))
                ),
            })

            for song_id, group in context_frame.groupby("song_id"):
                y = group[f"true_{target}"].to_numpy()
                p = group[f"pred_{target}"].to_numpy()

                per_song_rows.append({
                    "song_id": int(song_id),
                    "context_seconds": int(context),
                    "target": target,
                    "n": len(group),
                    "mae": float(np.mean(np.abs(y - p))),
                    "rmse": float(
                        np.sqrt(np.mean((y - p) ** 2))
                    ),
                })

    per_song = pd.DataFrame(per_song_rows)
    aggregate = pd.DataFrame(aggregate_rows)

    rng = np.random.default_rng(SEED)

    comparisons = []

    for target in TARGETS:
        for context_a, context_b in (
            (3, 5),
            (5, 8),
            (3, 8),
        ):
            comparisons.append(
                bootstrap_paired_song_mae(
                    per_song,
                    context_a,
                    context_b,
                    target,
                    rng,
                )
            )

    paired = pd.DataFrame(comparisons)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    predictions.to_csv(
        OUTPUT_DIR / "EXP_CONTEXT_paired_predictions.csv",
        index=False,
    )

    per_song.to_csv(
        OUTPUT_DIR / "EXP_CONTEXT_paired_per_song.csv",
        index=False,
    )

    aggregate.to_csv(
        OUTPUT_DIR / "EXP_CONTEXT_paired_aggregate.csv",
        index=False,
    )

    paired.to_csv(
        OUTPUT_DIR / "EXP_CONTEXT_paired_bootstrap.csv",
        index=False,
    )

    print("\n===== AGGREGATE METRICS =====")
    print(aggregate.to_string(index=False))

    print("\n===== PAIRED SONG-LEVEL COMPARISON =====")
    print(paired.to_string(index=False))

    print("\nInterpretation:")
    print("Positive improvement means context B is better.")
    print("Bootstrap CI is based on paired song-level MAE.")
    print("Context and selected layer may both differ.")
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
