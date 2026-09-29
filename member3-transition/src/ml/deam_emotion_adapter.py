def map_valence_arousal_to_emotion(valence, arousal):
    """
    Convert continuous DEAM valence/arousal values into
    a simple categorical emotion for offline testing.

    This is a testing proxy, not a DEAM ground-truth label.
    """

    if valence >= 0 and arousal >= 0:
        return "Excited"

    if valence >= 0 and arousal < 0:
        return "Calm"

    if valence < 0 and arousal >= 0:
        return "Tense"

    return "Sad"