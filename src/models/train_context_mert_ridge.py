
from pathlib import Path
import argparse
import time

import joblib
import numpy as np
import pandas as pd
import yaml

from scipy.stats import pearsonr
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = ROOT / "configs/mert_baseline_v1.yaml"

EXPECTED_TRAIN = 88153
EXPECTED_VALIDATION = 19965
EXPECTED_SONGS = 1531


def ccc_score(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    mean_true = np.mean(y_true)
    mean_pred = np.mean(y_pred)

    var_true = np.var(y_true)
    var_pred = np.var(y_pred)

    covariance = np.mean(
        (y_true - mean_true) * (y_pred - mean_pred)
    )

    denominator = (
        var_true + var_pred
        + (mean_true - mean_pred) ** 2
    )

    if denominator == 0:
        return np.nan

    return float(2.0 * covariance / denominator)


def calculate_metrics(y_true, y_pred):
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(
            np.sqrt(mean_squared_error(y_true, y_pred))
        ),
        "pearson": float(pearsonr(y_true, y_pred).statistic),
        "ccc": ccc_score(y_true, y_pred),
        "r2": float(r2_score(y_true, y_pred)),
    }


def load_layer(chunk_dir, layer):
    files = sorted(chunk_dir.glob("song_*.npz"))

    assert len(files) == EXPECTED_SONGS, (
        f"Expected {EXPECTED_SONGS} chunks, found {len(files)}"
    )

    train_x, val_x = [], []
    train_yv, val_yv = [], []
    train_ya, val_ya = [], []

    train_songs = set()
    val_songs = set()

    for path in files:
        with np.load(path, allow_pickle=False) as data:
            split = data["split"].astype(str)
            song_ids = data["song_id"]
            x = data[f"layer_{layer}"]
            yv = data["valence"]
            ya = data["arousal"]

            assert x.ndim == 2 and x.shape[1] == 768
            assert x.dtype == np.float32
            assert np.isfinite(x).all()
            assert np.isfinite(yv).all()
            assert np.isfinite(ya).all()

            assert len(x) == len(yv) == len(ya)
            assert len(song_ids) == len(x)

            unique_splits = set(np.unique(split))
            assert len(unique_splits) == 1
            assert unique_splits <= {"train", "validation"}

            unique_songs = set(np.unique(song_ids))
            assert len(unique_songs) == 1

            song_id = int(next(iter(unique_songs)))
            assert path.name == f"song_{song_id:04d}.npz"

            if "train" in unique_splits:
                assert song_id not in train_songs
                train_songs.add(song_id)
                train_x.append(x)
                train_yv.append(yv)
                train_ya.append(ya)
            else:
                assert song_id not in val_songs
                val_songs.add(song_id)
                val_x.append(x)
                val_yv.append(yv)
                val_ya.append(ya)

    assert train_songs.isdisjoint(val_songs)
    assert len(train_songs) == 1261
    assert len(val_songs) == 270

    X_train = np.concatenate(train_x).astype(np.float32)
    X_val = np.concatenate(val_x).astype(np.float32)

    yv_train = np.concatenate(train_yv)
    yv_val = np.concatenate(val_yv)
    ya_train = np.concatenate(train_ya)
    ya_val = np.concatenate(val_ya)

    assert X_train.shape == (EXPECTED_TRAIN, 768)
    assert X_val.shape == (EXPECTED_VALIDATION, 768)

    return (
        X_train,
        X_val,
        yv_train,
        yv_val,
        ya_train,
        ya_val,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--context-seconds",
        type=int,
        choices=[3, 8],
        required=True,
    )

    args = parser.parse_args()

    experiment_id = f"EXP_CONTEXT_{args.context_seconds}S"

    chunk_dir = (
        ROOT / "outputs" / "embeddings"
        / experiment_id / "chunks"
    )

    result_path = (
        ROOT / "outputs" / "results"
        / f"{experiment_id}_validation.csv"
    )

    model_dir = (
        ROOT / "outputs" / "models" / experiment_id
    )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    layers = config["representation"]["candidate_layers"]
    alphas = [
        float(a)
        for a in config["regression"]["alpha_candidates"]
    ]

    assert layers == [4, 8, 12]
    assert alphas == [0.01, 0.1, 1.0, 10.0, 100.0]

    if not chunk_dir.is_dir():
        raise FileNotFoundError(chunk_dir)

    rows = []
    best_models = {}

    print(f"===== {experiment_id} =====")
    print("Model: Frozen MERT + Ridge")
    print("Context:", args.context_seconds, "seconds")
    print("Layers:", layers)
    print("Alpha candidates:", alphas)
    print("TEST: LOCKED / NOT EVALUATED")

    for layer in layers:
        print(f"\n===== LAYER {layer} =====")

        (
            X_train,
            X_val,
            yv_train,
            yv_val,
            ya_train,
            ya_val,
        ) = load_layer(chunk_dir, layer)

        print("TRAIN:", X_train.shape)
        print("VALIDATION:", X_val.shape)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        assert scaler.n_samples_seen_ == EXPECTED_TRAIN

        best_valence = None
        best_arousal = None

        for alpha in alphas:
            start = time.perf_counter()

            v_model = Ridge(alpha=alpha)
            a_model = Ridge(alpha=alpha)

            v_model.fit(X_train_scaled, yv_train)
            a_model.fit(X_train_scaled, ya_train)

            v_pred = v_model.predict(X_val_scaled)
            a_pred = a_model.predict(X_val_scaled)

            elapsed = time.perf_counter() - start

            vm = calculate_metrics(yv_val, v_pred)
            am = calculate_metrics(ya_val, a_pred)

            rows.append({
                "experiment_id": experiment_id,
                "context_seconds": args.context_seconds,
                "layer": layer,
                "alpha": alpha,
                "mae_valence": vm["mae"],
                "mae_arousal": am["mae"],
                "rmse_valence": vm["rmse"],
                "rmse_arousal": am["rmse"],
                "pearson_valence": vm["pearson"],
                "pearson_arousal": am["pearson"],
                "ccc_valence": vm["ccc"],
                "ccc_arousal": am["ccc"],
                "r2_valence": vm["r2"],
                "r2_arousal": am["r2"],
                "fit_predict_seconds": elapsed,
            })

            if (
                best_valence is None
                or vm["mae"] < best_valence["mae"]
            ):
                best_valence = {
                    "mae": vm["mae"],
                    "alpha": alpha,
                    "model": v_model,
                }

            if (
                best_arousal is None
                or am["mae"] < best_arousal["mae"]
            ):
                best_arousal = {
                    "mae": am["mae"],
                    "alpha": alpha,
                    "model": a_model,
                }

            print(
                f"alpha={alpha:g} | "
                f"V MAE={vm['mae']:.6f}, "
                f"CCC={vm['ccc']:.6f} | "
                f"A MAE={am['mae']:.6f}, "
                f"CCC={am['ccc']:.6f}"
            )

        layer_dir = model_dir / f"layer_{layer}"
        layer_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            scaler,
            layer_dir / "scaler.joblib",
        )

        joblib.dump(
            best_valence["model"],
            layer_dir / "valence_ridge.joblib",
        )

        joblib.dump(
            best_arousal["model"],
            layer_dir / "arousal_ridge.joblib",
        )

        best_models[layer] = {
            "valence": {
                "alpha": best_valence["alpha"],
                "mae": best_valence["mae"],
            },
            "arousal": {
                "alpha": best_arousal["alpha"],
                "mae": best_arousal["mae"],
            },
        }

        print(
            f"Layer {layer} selected | "
            f"V alpha={best_valence['alpha']:g} | "
            f"A alpha={best_arousal['alpha']:g}"
        )

    assert len(rows) == 15

    results = pd.DataFrame(rows)

    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(result_path, index=False)

    selected_rows = []

    for target in ("valence", "arousal"):
        metric = f"mae_{target}"

        winner = results.sort_values(
            [metric, "layer", "alpha"],
            ascending=[True, True, True],
        ).iloc[0]

        selected_rows.append({
            "experiment_id": experiment_id,
            "context_seconds": args.context_seconds,
            "target": target,
            "layer": int(winner["layer"]),
            "alpha": float(winner["alpha"]),
            "mae": float(winner[metric]),
            "rmse": float(winner[f"rmse_{target}"]),
            "pearson": float(winner[f"pearson_{target}"]),
            "ccc": float(winner[f"ccc_{target}"]),
            "r2": float(winner[f"r2_{target}"]),
        })

    selected = pd.DataFrame(selected_rows)

    selected_path = (
        result_path.parent
        / f"{experiment_id}_selected.csv"
    )

    selected.to_csv(selected_path, index=False)

    print("\n===== SELECTED VALIDATION MODELS =====")
    print(selected.to_string(index=False))

    print("\nFull results:", result_path)
    print("Selected models:", selected_path)
    print("Model directory:", model_dir)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
