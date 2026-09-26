class TransitionScorer:
    def __init__(self):
        pass

    def calculate_score(
        self,
        emotion_change=False,
        confidence=0.0,
        persistence=0.0,
        beat=False,
        downbeat=False,
        onset=False,
        energy_change=False
    ):
        score = 0.0

        if emotion_change:
            score += 0.30

        if confidence >= 0.70:
            score += 0.20

        if persistence >= 0.70:
            score += 0.15

        if downbeat:
            score += 0.15

        elif beat:
            score += 0.10

        if onset:
            score += 0.05

        if energy_change:
            score += 0.05

        return round(score, 2)