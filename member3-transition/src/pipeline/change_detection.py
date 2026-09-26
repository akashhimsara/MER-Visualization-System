class MeaningfulChangeDetector:
    def __init__(self, confidence_threshold=0.70):
        self.confidence_threshold = confidence_threshold

    def is_meaningful(self, previous_emotion, current_emotion, current_confidence):
        if previous_emotion == current_emotion:
            return False

        if current_confidence < self.confidence_threshold:
            return False

        return True