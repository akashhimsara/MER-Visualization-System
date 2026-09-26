from collections import Counter


class TemporalAnalyzer:
    def __init__(self):
        self.history = []

    def add(self, timestamp, emotion, confidence):
        self.history.append({
            "timestamp": timestamp,
            "emotion": emotion,
            "confidence": confidence
        })
    def calculate_change_count(self):
        if len(self.history) < 2:
            return 0

        change_count = 0

        for i in range(1, len(self.history)):
            previous_emotion = self.history[i - 1]["emotion"]
            current_emotion = self.history[i]["emotion"]

            if previous_emotion != current_emotion:
                change_count += 1

        return change_count
    
    def analyze(self):
        if not self.history:
            return None

        emotions = [item["emotion"] for item in self.history]
        confidences = [item["confidence"] for item in self.history]

        emotion_counts = Counter(emotions)
        dominant_emotion = emotion_counts.most_common(1)[0][0]

        average_confidence = sum(confidences) / len(confidences)

        return {
            "dominant_emotion": dominant_emotion,
            "average_confidence": round(average_confidence, 2),
            "sample_count": len(self.history),
            "change_count": self.calculate_change_count()
        }