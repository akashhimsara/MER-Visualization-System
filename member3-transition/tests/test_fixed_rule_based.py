from src.baselines.fixed_rule_based import FixedRuleBasedBaseline


baseline = FixedRuleBasedBaseline()

assert baseline.should_transition(
    emotion_changed=False,
    confidence=0.90
) is False

assert baseline.should_transition(
    emotion_changed=True,
    confidence=0.60,
    beat=True
) is False

assert baseline.should_transition(
    emotion_changed=True,
    confidence=0.90,
    beat=False,
    downbeat=False
) is False

assert baseline.should_transition(
    emotion_changed=True,
    confidence=0.90,
    beat=True
) is True

assert baseline.should_transition(
    emotion_changed=True,
    confidence=0.90,
    downbeat=True
) is True

print("Fixed Rule-Based Baseline test passed!")