class ImmediateReactiveBaseline:
    def should_transition(self, previous_emotion, current_emotion):
        if previous_emotion is None:
            return False

        return previous_emotion != current_emotion