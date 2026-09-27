class FixedRuleBasedBaseline:
    def should_transition(
        self,
        emotion_changed,
        confidence,
        beat=False,
        downbeat=False
    ):
        if not emotion_changed:
            return False

        if confidence < 0.70:
            return False

        if downbeat:
            return True

        if beat:
            return True

        return False