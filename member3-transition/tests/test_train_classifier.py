from src.ml.train_classifier import train_logistic_regression

X = [
    [1, 0.90, 0.80, 1, 0.75, 1],
    [1, 0.95, 0.90, 1, 0.85, 1],
    [0, 0.85, 1.00, 0, 0.20, 1],
    [1, 0.60, 0.50, 1, 0.30, 1],
    [0, 0.90, 0.40, 1, 0.40, 1],
    [0, 0.95, 0.30, 0, 0.25, 1],
]
Y = [1, 1, 0, 0, 0, 0]


def test_train_logistic_regression():
    model = train_logistic_regression(X, Y)
    predictions = model.predict(X)

    assert len(predictions) == len(Y)
    assert set(predictions).issubset({0, 1})