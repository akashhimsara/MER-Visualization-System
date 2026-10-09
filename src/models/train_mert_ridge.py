
from pathlib import Path
import sys
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
CHUNK_DIR = (
    ROOT
    / "outputs/embeddings/EXP_MERT_001/chunks"
)
RESULT_PATH = (
    ROOT
    / "outputs/results/EXP_MERT_001_validation.csv"
)
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"

EXPECTED_TRAIN = 88153
EXPECTED_VALIDATION = 19965
EXPECTED_TOTAL = EXPECTED_TRAIN + EXPECTED_VALIDATION
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


def load_layer(layer):
    files = sorted(CHUNK_DIR.glob("song_*.npz"))

    assert len(files) == EXPECTED_SONGS, (
        f"Expected {EXPECTED_SONGS} chunks, found {len(files)}"
    )

    train_x = []
    val_x = []

    train_yv = []
    val_yv = []

    train_ya = []
    val_ya = []

    for path in files:
        with np.load(path, allow_pickle=False) as data:
            split = data["split"].astype(str)
            x = data[f"layer_{layer}"]

            yv = data["valence"]
            ya = data["arousal"]

            assert x.ndim == 2 and x.shape[1] == 768
            assert x.dtype == np.float32
            assert np.isfinite(x).all()
            assert np.isfinite(yv).all()
            assert np.isfinite(ya).all()

            unique_splits = set(np.unique(split))
            assert unique_splits <= {"train", "validation"}, (
                path,
                unique_splits,
            )

            assert len(unique_splits) == 1, path

            if "train" in unique_splits:
                train_x.append(x)
                train_yv.append(yv)
                train_ya.append(ya)
            else:
                val_x.append(x)
                val_yv.append(yv)
                val_ya.append(ya)

    X_train = np.concatenate(train_x).astype(np.float32)
    X_val = np.concatenate(val_x).astype(np.float32)

    yv_train = np.concatenate(train_yv)
    yv_val = np.concatenate(val_yv)

    ya_train = np.concatenate(train_ya)
    ya_val = np.concatenate(val_ya)

    assert X_train.shape == (EXPECTED_TRAIN, 768)
    assert X_val.shape == (EXPECTED_VALIDATION, 768)

    assert len(yv_train) == EXPECTED_TRAIN
    assert len(ya_train) == EXPECTED_TRAIN
    assert len(yv_val) == EXPECTED_VALIDATION
    assert len(ya_val) == EXPECTED_VALIDATION

    return (
        X_train,
        X_val,
        yv_train,
        yv_val,
        ya_train,
        ya_val,
    )


def main():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    layers = config["representation"]["candidate_layers"]
    alphas = config["regression"]["alpha_candidates"]

    assert layers == [4, 8, 12]
    assert [float(a) for a in alphas] == [
        0.01, 0.1, 1.0, 10.0, 100.0
    ]

    rows = []

    print("===== EXP_MERT_001 =====")
    print("Model: Frozen MERT + Ridge")
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
        ) = load_layer(layer)

        print("TRAIN:", X_train.shape)
        print("VALIDATION:", X_val.shape)

        scaler = StandardScaler()

        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        assert scaler.n_samples_seen_ == EXPECTED_TRAIN

        layer_dir = MODEL_DIR / f"layer_{layer}"
        layer_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            scaler,
            layer_dir / "scaler.joblib",
        )

        for alpha in alphas:
            alpha = float(alpha)
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
                "experiment_id": "EXP_MERT_001",
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

            print(
                f"alpha={alpha:g} | "
                f"V MAE={vm['mae']:.6f}, "
                f"CCC={vm['ccc']:.6f} | "
                f"A MAE={am['mae']:.6f}, "
                f"CCC={am['ccc']:.6f}"
            )

    assert len(rows) == 15

    results = pd.DataFrame(rows)

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(RESULT_PATH, index=False)

    print("\n===== VALIDATION SUMMARY =====")
    print(
        results[
            [
                "layer",
                "alpha",
                "mae_valence",
                "mae_arousal",
                "ccc_valence",
                "ccc_arousal",
            ]
        ].to_string(index=False)
    )

    print("\nResults saved:", RESULT_PATH)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
