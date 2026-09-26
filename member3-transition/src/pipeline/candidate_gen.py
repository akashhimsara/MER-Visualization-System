class TransitionCandidateGenerator:
    def __init__(self):
        pass

    def is_candidate(
        self,
        beat=False,
        downbeat=False,
        onset=False,
        section_boundary=False,
        energy_change=False
    ):
        if downbeat:
            return True

        if section_boundary:
            return True

        if beat:
            return True

        if onset:
            return True

        if energy_change:
            return True

        return False