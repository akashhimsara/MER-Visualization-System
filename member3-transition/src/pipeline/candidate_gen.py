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

    def classify_candidate_type(
        self,
        beat=False,
        downbeat=False,
        onset=False,
        section_boundary=False,
        energy_change=False
    ):
        """
        Which musical landmark triggered the candidate - used only to pick
        the transition's SCALE (major vs minor), never to decide whether
        to transition at all. Priority order matches is_candidate() above:
        bigger structural landmarks win over smaller ones when more than
        one is true at once.
        """
        if downbeat:
            return "downbeat"
        if section_boundary:
            return "section_boundary"
        if beat:
            return "beat"
        if onset:
            return "onset"
        if energy_change:
            return "energy_change"
        return None