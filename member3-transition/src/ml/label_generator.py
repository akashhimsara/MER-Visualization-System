def generate_pseudo_label(result):
    """
    Generate a preliminary transition label using
    existing rule-based signals.

    1 = transition suitable
    0 = transition not suitable
    """

    if not result["emotion_changed"]:
        return 0

    if result["confidence"] < 0.70:
        return 0

    if result["persistence"] < 0.70:
        return 0

    if not result["candidate"]:
        return 0

    return 1