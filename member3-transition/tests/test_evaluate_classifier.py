from src.ml.train_classifier import train_logistic_regression
from src.ml.evaluate_classifier import evaluate_classifier

X_TRAIN = [
    [1, 0.90, 0.80, 1, 0.75, 1],
    [1, 0.95, 0.90, 1, 0.85, 1],
    [0, 0.85, 1.00, 0, 0.20, 1],
    [1, 0.60, 0.50, 1, 0.30, 1],
    [0, 0.90, 0.40, 1, 0.40, 1],
    [0, 0.95, 0.30, 0, 0.25, 1],
]
Y_TRAIN = [1, 1, 0, 0, 0, 0]

X_TEST = [
    [1, 0.92, 0.85, 1, 0.80, 1],
    [0, 0.88, 0.90, 0, 0.25, 1],
    [1, 0.65, 0.55, 1, 0.35, 1],
    [0, 0.93, 0.35, 0, 0.20, 1],
]
Y_TEST = [1, 0, 0, 0]


def test_evaluate_classifier_returns_valid_metrics():
    model = train_logistic_regression(X_TRAIN, Y_TRAIN)
    metrics = evaluate_classifier(model, X_TEST, Y_TEST)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics

    for key in ("accuracy", "precision", "recall", "f1_score"):
        assert 0.0 <= metrics[key] <= 1.0