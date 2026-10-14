
from pathlib import Path
import csv
import sys

import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.features.hybrid_features import load_hybrid_features

RESULTS_DIR = ROOT / "outputs" / "results"
MODELS_DIR = ROOT / "outputs" / "models" / "EXP_HYBRID_001"

LAYERS = [4, 8]
ALPHAS = [0.01, 0.1, 1.0, 10.0, 100.0]


def calculate_metrics(y_true, y_pred):
    error = y_true - y_pred

    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(error ** 2)))

    if np.std(y_true) > 0 and np.std(y_pred) > 0:
        pearson = float(np.corrcoef(y_true, y_pred)[0, 1])
    else:
        pearson = 0.0

    mean_true = np.mean(y_true)
    mean_pred = np.mean(y_pred)

    var_true = np.var(y_true)
    var_pred = np.var(y_pred)

    covariance = np.mean(
        (y_true - mean_true) * (y_pred - mean_pred)
    )

    denominator = (
        var_true + var_pred + (mean_true - mean_pred) ** 2
    )

    ccc = (
        float(2 * covariance / denominator)
        if denominator > 0 else 0.0
    )

    ss_res = np.sum(error ** 2)
    ss_tot = np.sum((y_true - mean_true) ** 2)

    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "mae": mae,
        "rmse": rmse,
        "pearson": pearson,
        "ccc": ccc,
        "r2": r2,
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    rows = []

    for layer in LAYERS:
        print(f"\nLoading Hybrid Layer {layer}...")

        (
            X_train,
            X_val,
            yv_train,
            yv_val,
            ya_train,
            ya_val,
        ) = load_hybrid_features(layer)

        print("TRAIN:", X_train.shape)
        print("VALIDATION:", X_val.shape)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        layer_dir = MODELS_DIR / f"layer_{layer}"
        layer_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(scaler, layer_dir / "scaler.joblib")

        for alpha in ALPHAS:
            for target, y_train, y_val in [
                ("valence", yv_train, yv_val),
                ("arousal", ya_train, ya_val),
            ]:
                model = Ridge(alpha=alpha)
                model.fit(X_train_scaled, y_train)

                predictions = model.predict(X_val_scaled)
                metrics = calculate_metrics(y_val, predictions)

                row = {
                    "experiment_id": "EXP_HYBRID_001",
                    "layer": layer,
                    "alpha": alpha,
                    "target": target,
                    **metrics,
                }
                rows.append(row)

                print(
                    f"Layer={layer} "
                    f"Target={target} "
                    f"Alpha={alpha} "
                    f"MAE={metrics['mae']:.6f} "
                    f"CCC={metrics['ccc']:.6f}"
                )

    output_path = (
        RESULTS_DIR / "EXP_HYBRID_001_validation.csv"
    )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "experiment_id",
                "layer",
                "alpha",
                "target",
                "mae",
                "rmse",
                "pearson",
                "ccc",
                "r2",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSaved:", output_path)
    print("TEST partition used: NO")
    print("RESULT: TRAINING COMPLETE")


if __name__ == "__main__":
    main()
