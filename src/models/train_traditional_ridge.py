from pathlib import Path
import time

import numpy as np
import pandas as pd
import yaml
import joblib

from scipy.stats import pearsonr

from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import StandardScaler


CONFIG_PATH = Path(
    "configs/traditional_baseline_v1.yaml"
)

FEATURE_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
)

RESULT_PATH = Path(
    "outputs/results/EXP_TRAD_001_validation.csv"
)

MODEL_DIR = Path(
    "outputs/models/EXP_TRAD_001"
)


def concordance_correlation_coefficient(
    y_true,
    y_pred,
):
    y_true = np.asarray(
        y_true,
        dtype=np.float64,
    )

    y_pred = np.asarray(
        y_pred,
        dtype=np.float64,
    )

    mean_true = np.mean(y_true)
    mean_pred = np.mean(y_pred)

    var_true = np.var(y_true)
    var_pred = np.var(y_pred)

    covariance = np.mean(
        (y_true - mean_true)
        * (y_pred - mean_pred)
    )

    denominator = (
        var_true
        + var_pred
        + (mean_true - mean_pred) ** 2
    )

    if denominator == 0:
        return np.nan

    return (
        2.0 * covariance / denominator
    )


def calculate_metrics(
    y_true,
    y_pred,
):
    mae = mean_absolute_error(
        y_true,
        y_pred,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred,
        )
    )

    pearson = pearsonr(
        y_true,
        y_pred,
    ).statistic

    ccc = (
        concordance_correlation_coefficient(
            y_true,
            y_pred,
        )
    )

    r2 = r2_score(
        y_true,
        y_pred,
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "pearson": float(pearson),
        "ccc": float(ccc),
        "r2": float(r2),
    }


def main():

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        config = yaml.safe_load(f)

    alpha_candidates = config[
        "regression"
    ]["alpha_candidates"]

    artifact = np.load(
        FEATURE_PATH,
        allow_pickle=False,
    )

    X = artifact["X"]
    valence = artifact["valence"]
    arousal = artifact["arousal"]
    split = artifact["split"].astype(str)

    train_mask = split == "train"
    val_mask = split == "validation"

    # IMPORTANT:
    # No TEST arrays are created here.

    X_train = X[train_mask]
    X_val = X[val_mask]

    yv_train = valence[train_mask]
    yv_val = valence[val_mask]

    ya_train = arousal[train_mask]
    ya_val = arousal[val_mask]

    print("===== EXP_TRAD_001 =====")
    print("Model: Ridge Regression")
    print("TRAIN:", X_train.shape)
    print("VALIDATION:", X_val.shape)
    print("TEST: LOCKED / NOT EVALUATED")

    # ---------------------------------------------
    # TRAIN-only scaling
    # ---------------------------------------------

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    X_val_scaled = scaler.transform(
        X_val
    )

    results = []

    # ---------------------------------------------
    # Candidate alpha evaluation
    # ---------------------------------------------

    for alpha in alpha_candidates:

        print(
            f"\n----- alpha={alpha} -----"
        )

        start = time.perf_counter()

        valence_model = Ridge(
            alpha=float(alpha)
        )

        arousal_model = Ridge(
            alpha=float(alpha)
        )

        valence_model.fit(
            X_train_scaled,
            yv_train,
        )

        arousal_model.fit(
            X_train_scaled,
            ya_train,
        )

        valence_pred = (
            valence_model.predict(
                X_val_scaled
            )
        )

        arousal_pred = (
            arousal_model.predict(
                X_val_scaled
            )
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        v_metrics = calculate_metrics(
            yv_val,
            valence_pred,
        )

        a_metrics = calculate_metrics(
            ya_val,
            arousal_pred,
        )

        row = {
            "experiment_id": "EXP_TRAD_001",
            "model": "Ridge",
            "alpha": float(alpha),

            "mae_valence":
                v_metrics["mae"],
            "mae_arousal":
                a_metrics["mae"],

            "rmse_valence":
                v_metrics["rmse"],
            "rmse_arousal":
                a_metrics["rmse"],

            "pearson_valence":
                v_metrics["pearson"],
            "pearson_arousal":
                a_metrics["pearson"],

            "ccc_valence":
                v_metrics["ccc"],
            "ccc_arousal":
                a_metrics["ccc"],

            "r2_valence":
                v_metrics["r2"],
            "r2_arousal":
                a_metrics["r2"],

            "fit_predict_seconds":
                elapsed,
        }

        results.append(row)

        print(
            "Valence | "
            f"MAE={v_metrics['mae']:.6f} | "
            f"RMSE={v_metrics['rmse']:.6f} | "
            f"r={v_metrics['pearson']:.6f} | "
            f"CCC={v_metrics['ccc']:.6f} | "
            f"R2={v_metrics['r2']:.6f}"
        )

        print(
            "Arousal | "
            f"MAE={a_metrics['mae']:.6f} | "
            f"RMSE={a_metrics['rmse']:.6f} | "
            f"r={a_metrics['pearson']:.6f} | "
            f"CCC={a_metrics['ccc']:.6f} | "
            f"R2={a_metrics['r2']:.6f}"
        )

    # ---------------------------------------------
    # Save validation results
    # ---------------------------------------------

    results_df = pd.DataFrame(
        results
    )

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_df.to_csv(
        RESULT_PATH,
        index=False,
    )
        # ---------------------------------------------
    # Refit selected validation-derived models
    # ---------------------------------------------

    selected_config = config[
        "regression"
    ]["selected"]

    valence_alpha = float(
        selected_config["valence_alpha"]
    )

    arousal_alpha = float(
        selected_config["arousal_alpha"]
    )

    selected_valence_model = Ridge(
        alpha=valence_alpha
    )

    selected_arousal_model = Ridge(
        alpha=arousal_alpha
    )

    selected_valence_model.fit(
        X_train_scaled,
        yv_train,
    )

    selected_arousal_model.fit(
        X_train_scaled,
        ya_train,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        scaler,
        MODEL_DIR / "scaler.joblib",
    )

    joblib.dump(
        selected_valence_model,
        MODEL_DIR / "valence_ridge.joblib",
    )

    joblib.dump(
        selected_arousal_model,
        MODEL_DIR / "arousal_ridge.joblib",
    )

    print("\nSelected configuration")
    print(
        "Valence alpha:",
        valence_alpha,
    )
    print(
        "Arousal alpha:",
        arousal_alpha,
    )

    print(
        "Artifacts:",
        MODEL_DIR,
    )

    print("\n===== COMPLETE =====")
    print(
        "Validation results:",
        RESULT_PATH,
    )

    print(
        "TEST partition was not evaluated."
    )


if __name__ == "__main__":
    main()