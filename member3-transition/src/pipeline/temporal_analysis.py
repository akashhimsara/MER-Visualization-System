from collections import Counter, deque


class TemporalAnalyzer:
    def __init__(self, window_size=50):
        # FIX: this was a plain unbounded list before - every frame since
        # the start of the song stayed in memory forever, and
        # calculate_persistence()/calculate_change_count() re-scanned the
        # WHOLE thing on every single call. For a real-time system meant
        # to run for the length of a song (or longer, across songs in one
        # session), that's an unbounded, ever-slowing operation - exactly
        # what NFR01/NFR02 (real-time responsiveness, low latency) rule
        # out. A bounded deque, same pattern already used correctly in
        # smoothing.py, fixes both the memory growth and makes
        # "persistence" mean what it should: how stable the emotion has
        # been RECENTLY, not what fraction of the entire song-so-far it
        # dominated (which makes the number less and less sensitive to
        # real change the longer a session runs).
        self.history = deque(maxlen=window_size)

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
            "change_count": self.calculate_change_count(),
            "persistence": self.calculate_persistence(dominant_emotion)
        }
    def calculate_persistence(self, emotion):
        if not self.history:
            return 0.0

        matching_count = 0

        for item in self.history:
            if item["emotion"] == emotion:
                matching_count += 1

        persistence = matching_count / len(self.history)

        return round(persistence, 2)    