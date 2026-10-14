
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.features.hybrid_features import load_hybrid_features

RESULTS_FILE = (
    ROOT / "outputs/results/EXP_HYBRID_001_validation.csv"
)

MODELS_DIR = (
    ROOT / "outputs/models/EXP_HYBRID_001"
)

SELECTED = {
    "valence": {"layer": 4, "alpha": 100.0},
    "arousal": {"layer": 8, "alpha": 100.0},
}


def main():
    results = pd.read_csv(RESULTS_FILE)

    assert len(results) == 20, "Unexpected experiment count"

    for target, config in SELECTED.items():
        layer = config["layer"]
        alpha = config["alpha"]

        matching = results[
            (results["target"] == target)
            & (results["layer"] == layer)
            & (np.isclose(results["alpha"], alpha))
        ]

        assert len(matching) == 1, (
            f"Selected configuration missing: {target}"
        )

        print(f"\nSaving {target} model — Layer {layer}")

        (
            X_train,
            X_val,
            yv_train,
            yv_val,
            ya_train,
            ya_val,
        ) = load_hybrid_features(layer)

        y_train = yv_train if target == "valence" else ya_train
        y_val = yv_val if target == "valence" else ya_val

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        model = Ridge(alpha=alpha)
        model.fit(X_train_scaled, y_train)

        predictions = model.predict(X_val_scaled)

        mae = float(np.mean(np.abs(y_val - predictions)))
        expected_mae = float(matching.iloc[0]["mae"])

        print(f"Expected MAE: {expected_mae:.6f}")
        print(f"Actual MAE:   {mae:.6f}")

        assert abs(mae - expected_mae) < 1e-5, (
            f"Validation MAE mismatch for {target}"
        )

        output_dir = MODELS_DIR / f"layer_{layer}"
        output_dir.mkdir(parents=True, exist_ok=True)

        scaler_path = output_dir / "scaler.joblib"
        model_path = output_dir / f"{target}_ridge.joblib"

        joblib.dump(scaler, scaler_path)
        joblib.dump(model, model_path)

        # Verify saved artifacts can be reloaded.
        loaded_scaler = joblib.load(scaler_path)
        loaded_model = joblib.load(model_path)

        reloaded_predictions = loaded_model.predict(
            loaded_scaler.transform(X_val)
        )

        np.testing.assert_allclose(
            predictions,
            reloaded_predictions,
            rtol=1e-6,
            atol=1e-6,
        )

        print(f"Saved scaler: {scaler_path}")
        print(f"Saved model:  {model_path}")
        print("Reload prediction equivalence: PASS")

    print("\nTEST partition used: NO")
    print("RESULT: SELECTED HYBRID MODELS SAVED")


if __name__ == "__main__":
    main()
