FEATURE_ORDER = [
    "emotion_changed",
    "confidence",
    "persistence",
    "candidate",
    "score",
    "can_transition",
]


def _to_feature_vector(result):
    return [[
        int(bool(result["emotion_changed"])),
        float(result["confidence"]),
        float(result["persistence"]),
        int(bool(result["candidate"])),
        float(result["score"]),
        int(bool(result["can_transition"])),
    ]]


def predict_transition_suitability(model, result):
    """
    Use the trained Logistic Regression model to estimate
    whether the current frame is suitable for a transition.
    """

    features = _to_feature_vector(result)

    prediction = int(model.predict(features)[0])

    if hasattr(model, "predict_proba"):
        probability = float(
            model.predict_proba(features)[0][1]
        )
    else:
        probability = float(prediction)

    return {
        "suitable": prediction == 1,
        "probability": round(probability, 3),
    }