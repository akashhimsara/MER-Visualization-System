import joblib

from sklearn.linear_model import LogisticRegression


def train_logistic_regression(X, y):
    model = LogisticRegression()

    model.fit(X, y)

    return model


if __name__ == "__main__":

    X = [
        [1, 0.90, 0.80, 1, 0.75, 1],
        [1, 0.95, 0.90, 1, 0.85, 1],
        [0, 0.85, 1.00, 0, 0.20, 1],
        [1, 0.60, 0.50, 1, 0.30, 1],
        [0, 0.90, 0.40, 1, 0.40, 1],
        [0, 0.95, 0.30, 0, 0.25, 1],
    ]

    y = [
        1,
        1,
        0,
        0,
        0,
        0,
    ]

    model = train_logistic_regression(X, y)
    joblib.dump(model, "models/transition_model.pkl")
    print("Model saved to models/transition_model.pkl")

    print("Logistic Regression model trained successfully!")
    print("Training samples:", len(X))