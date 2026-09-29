from src.ml.train_classifier import train_logistic_regression
from src.ml.evaluate_classifier import evaluate_classifier


X_train = [
    [1, 0.90, 0.80, 1, 0.75, 1],
    [1, 0.95, 0.90, 1, 0.85, 1],
    [0, 0.85, 1.00, 0, 0.20, 1],
    [1, 0.60, 0.50, 1, 0.30, 1],
    [0, 0.90, 0.40, 1, 0.40, 1],
    [0, 0.95, 0.30, 0, 0.25, 1],
]

y_train = [1, 1, 0, 0, 0, 0]


X_test = [
    [1, 0.92, 0.85, 1, 0.80, 1],
    [0, 0.88, 0.90, 0, 0.25, 1],
    [1, 0.65, 0.55, 1, 0.35, 1],
    [0, 0.93, 0.35, 0, 0.20, 1],
]

y_test = [1, 0, 0, 0]


model = train_logistic_regression(
    X_train,
    y_train
)

metrics = evaluate_classifier(
    model,
    X_test,
    y_test
)

assert "accuracy" in metrics
assert "precision" in metrics
assert "recall" in metrics
assert "f1_score" in metrics

assert 0.0 <= metrics["accuracy"] <= 1.0
assert 0.0 <= metrics["precision"] <= 1.0
assert 0.0 <= metrics["recall"] <= 1.0
assert 0.0 <= metrics["f1_score"] <= 1.0

print("ML evaluation test passed!")
print(metrics)