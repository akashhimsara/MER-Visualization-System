
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.hybrid_features import load_hybrid_features

RESULTS_FILE = (
    ROOT / "outputs/results/EXP_HYBRID_001_validation.csv"
)

MODELS_DIR = (
    ROOT / "outputs/models/EXP_HYBRID_001"
)

SELECTED = {
    "valence": (4, 100.0),
    "arousal": (8, 100.0),
}


def calculate_metrics(y_true, y_pred):
    error = y_true - y_pred

    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(error ** 2)))

    pearson = float(np.corrcoef(y_true, y_pred)[0, 1])

    mean_true = np.mean(y_true)
    mean_pred = np.mean(y_pred)

    covariance = np.mean(
        (y_true - mean_true) * (y_pred - mean_pred)
    )

    denominator = (
        np.var(y_true)
        + np.var(y_pred)
        + (mean_true - mean_pred) ** 2
    )

    ccc = float(2 * covariance / denominator)

    ss_res = np.sum(error ** 2)
    ss_tot = np.sum((y_true - mean_true) ** 2)

    r2 = float(1 - ss_res / ss_tot)

    return {
        "mae": mae,
        "rmse": rmse,
        "pearson": pearson,
        "ccc": ccc,
        "r2": r2,
    }


def main():
    results = pd.read_csv(RESULTS_FILE)

    for target, (layer, alpha) in SELECTED.items():
        print(f"\nChecking {target} — Layer {layer}")

        (
            X_train,
            X_val,
            yv_train,
            yv_val,
            ya_train,
            ya_val,
        ) = load_hybrid_features(layer)

        assert X_train.shape == (88153, 854)
        assert X_val.shape == (19965, 854)

        y_val = yv_val if target == "valence" else ya_val

        model_dir = MODELS_DIR / f"layer_{layer}"

        scaler = joblib.load(model_dir / "scaler.joblib")
        model = joblib.load(
            model_dir / f"{target}_ridge.joblib"
        )

        predictions = model.predict(
            scaler.transform(X_val)
        )

        assert np.isfinite(predictions).all()

        actual = calculate_metrics(y_val, predictions)

        matching = results[
            (results["target"] == target)
            & (results["layer"] == layer)
            & (np.isclose(results["alpha"], alpha))
        ]

        assert len(matching) == 1

        expected = matching.iloc[0]

        for metric, actual_value in actual.items():
            expected_value = float(expected[metric])

            np.testing.assert_allclose(
                actual_value,
                expected_value,
                rtol=1e-6,
                atol=1e-6,
                err_msg=f"{target}: {metric} mismatch",
            )

        print("All five validation metrics: PASS")
        print(f"MAE: {actual['mae']:.6f}")
        print(f"CCC: {actual['ccc']:.6f}")

    print("\nTEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
