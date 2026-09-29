from pathlib import Path
import sys

import joblib
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


FEATURE_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
)

MODEL_DIR = Path(
    "outputs/models/EXP_TRAD_001"
)


def ccc(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

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

    return 2.0 * covariance / denominator


def metrics(y_true, y_pred):
    return {
        "mae": mean_absolute_error(
            y_true, y_pred
        ),
        "rmse": np.sqrt(
            mean_squared_error(
                y_true, y_pred
            )
        ),
        "pearson": pearsonr(
            y_true, y_pred
        ).statistic,
        "ccc": ccc(
            y_true, y_pred
        ),
        "r2": r2_score(
            y_true, y_pred
        ),
    }


print("===== SAVED TRADITIONAL MODEL TEST =====")

artifact = np.load(
    FEATURE_PATH,
    allow_pickle=False,
)

X = artifact["X"]
valence = artifact["valence"]
arousal = artifact["arousal"]
split = artifact["split"].astype(str)

val_mask = split == "validation"

# TEST is not extracted/evaluated.
X_val = X[val_mask]
yv_val = valence[val_mask]
ya_val = arousal[val_mask]


scaler = joblib.load(
    MODEL_DIR / "scaler.joblib"
)

valence_model = joblib.load(
    MODEL_DIR / "valence_ridge.joblib"
)

arousal_model = joblib.load(
    MODEL_DIR / "arousal_ridge.joblib"
)


X_val_scaled = scaler.transform(
    X_val
)

valence_pred = valence_model.predict(
    X_val_scaled
)

arousal_pred = arousal_model.predict(
    X_val_scaled
)


v = metrics(
    yv_val,
    valence_pred,
)

a = metrics(
    ya_val,
    arousal_pred,
)


print("\nSaved configuration")
print("Valence alpha:", valence_model.alpha)
print("Arousal alpha:", arousal_model.alpha)
print("Scaler TRAIN samples:", scaler.n_samples_seen_)


print("\nValidation metrics")

print(
    "Valence | "
    f"MAE={v['mae']:.6f} | "
    f"RMSE={v['rmse']:.6f} | "
    f"r={v['pearson']:.6f} | "
    f"CCC={v['ccc']:.6f} | "
    f"R2={v['r2']:.6f}"
)

print(
    "Arousal | "
    f"MAE={a['mae']:.6f} | "
    f"RMSE={a['rmse']:.6f} | "
    f"r={a['pearson']:.6f} | "
    f"CCC={a['ccc']:.6f} | "
    f"R2={a['r2']:.6f}"
)


expected = {
    "valence": {
        "mae": 0.208435,
        "rmse": 0.270191,
        "pearson": 0.422887,
        "ccc": 0.321749,
        "r2": 0.167060,
    },
    "arousal": {
        "mae": 0.156690,
        "rmse": 0.198961,
        "pearson": 0.729456,
        "ccc": 0.699001,
        "r2": 0.523081,
    },
}


def close(actual, expected_value):
    return np.isclose(
        actual,
        expected_value,
        atol=1e-5,
        rtol=0.0,
    )


reproduced = (
    close(v["mae"], expected["valence"]["mae"])
    and close(v["rmse"], expected["valence"]["rmse"])
    and close(v["pearson"], expected["valence"]["pearson"])
    and close(v["ccc"], expected["valence"]["ccc"])
    and close(v["r2"], expected["valence"]["r2"])

    and close(a["mae"], expected["arousal"]["mae"])
    and close(a["rmse"], expected["arousal"]["rmse"])
    and close(a["pearson"], expected["arousal"]["pearson"])
    and close(a["ccc"], expected["arousal"]["ccc"])
    and close(a["r2"], expected["arousal"]["r2"])

    and float(scaler.n_samples_seen_) == 88153.0
    and float(valence_model.alpha) == 0.1
    and float(arousal_model.alpha) == 100.0
)


if reproduced:
    print(
        "\nRESULT: PASS - saved models reproduce "
        "the selected validation configuration"
    )
else:
    print("\nRESULT: REVIEW REQUIRED")

print("TEST partition was not evaluated.")