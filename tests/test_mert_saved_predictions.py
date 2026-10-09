
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))

from src.models.train_mert_ridge import (
    load_layer,
    calculate_metrics,
)

root = Path("outputs/models/EXP_MERT_001")
results = pd.read_csv(
    "outputs/results/EXP_MERT_001_validation.csv"
)

print("===== SAVED MERT PREDICTION VERIFICATION =====")

for target, layer in [
    ("valence", 4),
    ("arousal", 8),
]:
    folder = root / f"layer_{layer}"

    scaler = joblib.load(
        folder / "scaler.joblib"
    )

    model = joblib.load(
        folder / f"{target}_ridge.joblib"
    )

    (
        X_train,
        X_val,
        yv_train,
        yv_val,
        ya_train,
        ya_val,
    ) = load_layer(layer)

    y_true = (
        yv_val if target == "valence"
        else ya_val
    )

    predictions = model.predict(
        scaler.transform(X_val)
    )

    metrics = calculate_metrics(
        y_true,
        predictions,
    )

    reference = results[
        (results["layer"] == layer)
        & np.isclose(results["alpha"], 100.0)
    ]

    assert len(reference) == 1

    for metric in (
        "mae",
        "rmse",
        "pearson",
        "ccc",
        "r2",
    ):
        expected = float(
            reference.iloc[0][f"{metric}_{target}"]
        )

        actual = metrics[metric]

        assert np.isclose(
            actual,
            expected,
            rtol=0,
            atol=1e-6,
        ), (
            target,
            metric,
            actual,
            expected,
        )

    print(
        f"{target.upper()} | "
        f"Layer {layer} | "
        "All 5 metrics reproduced: PASS"
    )

print("TEST partition used: NO")
print("RESULT: PASS")
