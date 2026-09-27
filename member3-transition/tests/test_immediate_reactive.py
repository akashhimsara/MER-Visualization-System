from src.baselines.immediate_reactive import ImmediateReactiveBaseline


baseline = ImmediateReactiveBaseline()

assert baseline.should_transition(None, "Happy") is False
assert baseline.should_transition("Happy", "Happy") is False
assert baseline.should_transition("Happy", "Sad") is True
assert baseline.should_transition("Sad", "Excited") is True

print("Immediate Reactive Baseline test passed!")