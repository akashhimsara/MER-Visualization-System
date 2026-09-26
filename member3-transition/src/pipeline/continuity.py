class ContinuityController:
    def __init__(self, cooldown_seconds=5.0):
        self.cooldown_seconds = cooldown_seconds
        self.last_transition_time = None

    def can_transition(self, current_time):
        if self.last_transition_time is None:
            return True

        time_since_last_transition = (
            current_time - self.last_transition_time
        )

        return time_since_last_transition >= self.cooldown_seconds

    def record_transition(self, current_time):
        self.last_transition_time = current_time