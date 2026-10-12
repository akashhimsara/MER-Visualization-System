import csv
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold

from src.ml.build_deam_training_set import (
    FEATURE_COLUMNS,
    TRAINING_SET_PATH,
    build_training_set,
    save_training_set,
)

MODEL_PATH = Path("models/transition_model.pkl")
RESULTS_PATH = Path("results/ml_evaluation.json")
FOLDS = 5
CONFIDENCE_GATE = 0.70   # the rule-based gate already used by the change detector


def load_training_set(path=TRAINING_SET_PATH):
    with Path(path).open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    X = np.array([[float(r[c]) for c in FEATURE_COLUMNS] for r in rows])
    y = np.array([int(r["label"]) for r in rows])
    groups = np.array([int(r["song_id"]) for r in rows])
    return X, y, groups


def make_logistic_regression():
    return LogisticRegression(class_weight="balanced", max_iter=1000)


def make_random_forest():
    return RandomForestClassifier(
        n_estimators=200, min_samples_leaf=5,
        class_weight="balanced", random_state=0,
    )


def cross_validate(make_model, X, y, groups, folds=FOLDS):
    """Out-of-fold predictions, split by song."""
    predictions = np.zeros(len(y), dtype=int)
    probabilities = np.zeros(len(y))
    for train_idx, test_idx in GroupKFold(n_splits=folds).split(X, y, groups):
        assert not set(groups[train_idx]) & set(groups[test_idx]), "song leakage"
        model = make_model().fit(X[train_idx], y[train_idx])
        predictions[test_idx] = model.predict(X[test_idx])
        probabilities[test_idx] = model.predict_proba(X[test_idx])[:, 1]
    return predictions, probabilities


def summarise(y, predictions, probabilities=None):
    """
    allowed = the transitions this method lets through.
    unnecessary_transition_rate : allowed transitions that were really flicker
                                  (the proposal's 'unnecessary transition rate')
    missed_genuine_rate         : genuine sustained changes that were blocked
    """
    allowed = predictions == 1
    summary = {
        "accuracy": round(float(accuracy_score(y, predictions)), 3),
        "precision": round(float(precision_score(y, predictions, zero_division=0)), 3),
        "recall": round(float(recall_score(y, predictions, zero_division=0)), 3),
        "f1": round(float(f1_score(y, predictions, zero_division=0)), 3),
        "unnecessary_transition_rate": round(
            float(1 - precision_score(y, predictions, zero_division=0)) if allowed.any() else 0.0, 3
        ),
        "missed_genuine_rate": round(
            float(1 - recall_score(y, predictions, zero_division=0)), 3
        ),
        "transitions_allowed": int(allowed.sum()),
    }
    if probabilities is not None:
        summary["auc"] = round(float(roc_auc_score(y, probabilities)), 3)
    return summary


def print_table(results):
    header = (
        f"{'Method':34s}{'acc':>6s}{'prec':>7s}{'rec':>6s}{'f1':>6s}"
        f"{'auc':>6s}{'unnecessary':>13s}{'missed':>8s}{'allowed':>9s}"
    )
    print(header)
    print("-" * len(header))
    for name, r in results.items():
        auc = f"{r['auc']:.2f}" if "auc" in r else "  -"
        print(
            f"{name:34s}{r['accuracy']:6.2f}{r['precision']:7.2f}{r['recall']:6.2f}"
            f"{r['f1']:6.2f}{auc:>6s}{r['unnecessary_transition_rate']:13.2f}"
            f"{r['missed_genuine_rate']:8.2f}{r['transitions_allowed']:9d}"
        )


def main():
    if not Path(TRAINING_SET_PATH).exists():
        print("Training set not found - building it from real DEAM annotations...")
        save_training_set(build_training_set())

    X, y, groups = load_training_set()
    print(f"Real DEAM decision rows : {len(y)} from {len(set(groups))} songs")
    print(f"Sustained (suitable)    : {int(y.sum())} ({y.mean():.0%})")
    print(f"Flicker (not suitable)  : {int((1 - y).sum())}")
    print(f"Evaluation              : {FOLDS}-fold cross-validation, split BY SONG\n")

    results = {}

    all_pass = np.ones(len(y), dtype=int)
    results["Baseline A: no ML (allow all)"] = summarise(y, all_pass)

    confidence_rule = (X[:, FEATURE_COLUMNS.index("confidence")] >= CONFIDENCE_GATE).astype(int)
    results["Baseline B: confidence >= 0.70"] = summarise(y, confidence_rule)

    for name, make_model in (
        ("Logistic Regression (proposed)", make_logistic_regression),
        ("Random Forest (comparison)", make_random_forest),
    ):
        predictions, probabilities = cross_validate(make_model, X, y, groups)
        results[name] = summarise(y, predictions, probabilities)

    print_table(results)

    final_model = make_logistic_regression().fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_PATH)

    coefficients = dict(zip(FEATURE_COLUMNS, [round(float(c), 3) for c in final_model.coef_[0]]))
    print("\nFinal Logistic Regression coefficients (what the model learned):")
    for feature, value in coefficients.items():
        print(f"  {feature:16s} {value:+.3f}")
    print(f"\nModel saved to {MODEL_PATH}")

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "rows": int(len(y)),
                "songs": int(len(set(groups))),
                "sustained_share": round(float(y.mean()), 3),
                "folds": FOLDS,
                "feature_order": FEATURE_COLUMNS,
                "results": results,
                "final_model_coefficients": coefficients,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Evaluation saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()