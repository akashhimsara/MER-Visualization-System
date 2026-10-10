from src.baselines.fixed_rule_based import FixedRuleBasedBaseline


def test_no_transition_without_emotion_change():
    baseline = FixedRuleBasedBaseline()
    assert baseline.should_transition(emotion_changed=False, confidence=0.90) is False


def test_no_transition_on_low_confidence():
    baseline = FixedRuleBasedBaseline()
    assert baseline.should_transition(emotion_changed=True, confidence=0.60, beat=True) is False


def test_no_transition_without_a_musical_landmark():
    baseline = FixedRuleBasedBaseline()
    assert baseline.should_transition(
        emotion_changed=True, confidence=0.90, beat=False, downbeat=False
    ) is False


def test_transitions_on_beat():
    baseline = FixedRuleBasedBaseline()
    assert baseline.should_transition(emotion_changed=True, confidence=0.90, beat=True) is True


def test_transitions_on_downbeat():
    baseline = FixedRuleBasedBaseline()
    assert baseline.should_transition(emotion_changed=True, confidence=0.90, downbeat=True) is True