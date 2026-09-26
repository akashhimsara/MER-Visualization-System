from collections import defaultdict, deque


class EmotionSmoother:
    def __init__(self, window_size=3):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def add(self, emotion, confidence):
        self.history.append({
            "emotion": emotion,
            "confidence": confidence
        })

    def get_smoothed_emotion(self):
        if not self.history:
            return None

        scores = defaultdict(float)

        for item in self.history:
            scores[item["emotion"]] += item["confidence"]

        return max(scores, key=scores.get)