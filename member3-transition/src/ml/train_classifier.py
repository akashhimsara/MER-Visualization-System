from sklearn.linear_model import LogisticRegression


def train_logistic_regression(X, y):
    model = LogisticRegression()

    model.fit(X, y)

    return model


if __name__ == "__main__":
    print("This file only defines train_logistic_regression().")
    print("To train on real DEAM data run:  python -m src.ml.train_on_deam")