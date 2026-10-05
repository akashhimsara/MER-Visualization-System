"""Train and export the Member 2 visual-mapping regression baseline.

The input data is a documented researcher-created controlled baseline. This
script evaluates only held-out mapping records; it does not evaluate MER or
human visual preference.
"""

import json
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "src" / "ai" / "mapping_dataset_v1.json"
MODEL_PATH = ROOT / "src" / "ai" / "model_weights_v1.json"
SEED = 20261005
TARGET_NAMES = [
    "hue", "saturation", "brightness", "particleDensity", "particleSize",
    "particleSpeed", "motionIntensity", "lightIntensity", "bloomStrength",
]
FEATURE_NAMES = [
    "bias", "valence", "arousal", "valenceSquared", "valenceArousal", "arousalSquared"
]
RIDGE_ALPHA = 0.000001


def feature_matrix(records):
    """Return [V, A, V², V×A, A²]; Ridge manages the intercept separately."""
    valence = np.array([record["valence"] for record in records], dtype=float)
    arousal = np.array([record["arousal"] for record in records], dtype=float)
    return np.column_stack((valence, arousal, valence ** 2, valence * arousal, arousal ** 2))


def json_number(value):
    return round(float(value), 10)


def main():
    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    labels = [record["emotionCategory"] for record in records]
    indices = np.arange(len(records))

    train_indices, test_indices = train_test_split(
        indices,
        test_size=0.20,
        random_state=SEED,
        stratify=labels,
    )
    train_records = [records[index] for index in train_indices]
    test_records = [records[index] for index in test_indices]

    x_train = feature_matrix(train_records)
    x_test = feature_matrix(test_records)
    y_train = np.array([[record[name] for name in TARGET_NAMES] for record in train_records], dtype=float)
    y_test = np.array([[record[name] for name in TARGET_NAMES] for record in test_records], dtype=float)

    model = Ridge(alpha=RIDGE_ALPHA, fit_intercept=True)
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)

    weights = {}
    metrics = {}
    for column, target_name in enumerate(TARGET_NAMES):
        weights[target_name] = [
            json_number(model.intercept_[column]),
            *[json_number(coefficient) for coefficient in model.coef_[column]],
        ]
        metrics[target_name] = {
            "mae": json_number(mean_absolute_error(y_test[:, column], predicted[:, column])),
            "rmse": json_number(root_mean_squared_error(y_test[:, column], predicted[:, column])),
        }

    exported_model = {
        "modelVersion": "visual-mapping-regressor-v1",
        "datasetVersion": "mapping-v1",
        "recordSource": "researcher_created_controlled_baseline",
        "modelType": "scikit_learn_multi_output_ridge_regression",
        "trainingLibrary": {"scikitLearnVersion": sklearn.__version__, "numpyVersion": np.__version__},
        "featureNames": FEATURE_NAMES,
        "targetNames": TARGET_NAMES,
        "split": {
            "strategy": "scikit-learn fixed-seed stratified split by emotionCategory",
            "seed": SEED,
            "trainRecordIds": sorted(record["recordId"] for record in train_records),
            "heldOutTestRecordIds": sorted(record["recordId"] for record in test_records),
        },
        "training": {"recordCount": len(train_records), "ridgeAlpha": RIDGE_ALPHA},
        "evaluation": {"recordCount": len(test_records), "metrics": metrics},
        "weights": weights,
    }
    MODEL_PATH.write_text(json.dumps(exported_model, indent=2) + "\n", encoding="utf-8")
    print(f"Trained scikit-learn Ridge model on {len(train_records)} records.")
    print(f"Evaluated on {len(test_records)} held-out records.")
    print(f"Exported browser weights to {MODEL_PATH}")


if __name__ == "__main__":
    main()
