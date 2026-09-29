from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def evaluate_classifier(model, X_test, y_test):
    predictions = model.predict(X_test)

    return {
        "accuracy": round(accuracy_score(y_test, predictions), 2),
        "precision": round(
            precision_score(y_test, predictions, zero_division=0),
            2
        ),
        "recall": round(
            recall_score(y_test, predictions, zero_division=0),
            2
        ),
        "f1_score": round(
            f1_score(y_test, predictions, zero_division=0),
            2
        )
    }