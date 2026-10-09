
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
import yaml

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.models.train_mert_ridge import (
    load_layer,
    calculate_metrics,
    MODEL_DIR,
    RESULT_PATH,
)

CONFIG_PATH = ROOT / "configs/mert_baseline_v1.yaml"


def main():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    selected = config["regression"]["selected"]

    assert selected["selected_using"] == "validation"
    assert selected["selection_metric"] == "mae"
    assert selected["test_evaluated"] is False

    validation_results = pd.read_csv(RESULT_PATH)

    print("===== SAVE SELECTED MERT MODELS =====")
    print("TEST: LOCKED / NOT EVALUATED")

    for target in ("valence", "arousal"):
        layer = int(selected[f"{target}_layer"])
        alpha = float(selected[f"{target}_alpha"])

        (
            X_train,
            X_val,
            yv_train,
            yv_val,
            ya_train,
            ya_val,
        ) = load_layer(layer)

        if target == "valence":
            y_train = yv_train
            y_val = yv_val
        else:
            y_train = ya_train
            y_val = ya_val

        scaler = StandardScaler()

        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        assert scaler.n_samples_seen_ == len(X_train)

        model = Ridge(alpha=alpha)
        model.fit(X_train_scaled, y_train)

        predictions = model.predict(X_val_scaled)
        metrics = calculate_metrics(y_val, predictions)

        reference = validation_results[
            (validation_results["layer"] == layer)
            & np.isclose(
                validation_results["alpha"],
                alpha,
            )
        ]

        assert len(reference) == 1

        reference_mae = float(
            reference.iloc[0][f"mae_{target}"]
        )

        reference_ccc = float(
            reference.iloc[0][f"ccc_{target}"]
        )

        assert np.isclose(
            metrics["mae"],
            reference_mae,
            rtol=0,
            atol=1e-6,
        ), (target, "MAE mismatch")

        assert np.isclose(
            metrics["ccc"],
            reference_ccc,
            rtol=0,
            atol=1e-6,
        ), (target, "CCC mismatch")

        output_dir = MODEL_DIR / f"layer_{layer}"
        output_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(
            scaler,
            output_dir / "scaler.joblib",
        )

        joblib.dump(
            model,
            output_dir / f"{target}_ridge.joblib",
        )

        print(
            f"{target.upper()} | "
            f"Layer={layer} | "
            f"Alpha={alpha:g} | "
            f"MAE={metrics['mae']:.6f} | "
            f"CCC={metrics['ccc']:.6f} | "
            "PASS"
        )

    print("\nTEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
