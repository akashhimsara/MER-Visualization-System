"""
Covers two things:
1. The fix to the "transition fires without an emotion change" bug.
2. The new build_transition_command() output shape (FR13).
"""
from src.pipeline.orchestrator import TransitionOrchestrator
from src.pipeline.transition_command import build_transition_command


def test_no_transition_without_emotion_change_even_with_strong_musical_signals():
    """
    This is the regression test for the bug: before the fix, confidence
    (0.20) + persistence (0.15) + downbeat (0.15) + onset (0.05) +
    energy_change (0.05) = 0.60 cleared the 0.50 threshold on musical
    signals alone, with no emotion change at all.
    """
    orchestrator = TransitionOrchestrator()
    for i in range(1, 10):
        result = orchestrator.process_frame(
            timestamp=i * 10.0,
            emotion="Calm",          # never changes
            confidence=0.95,
            beat=True, downbeat=True, onset=True, energy_change=True,
        )
        assert result["transition"] is False, (
            f"transitioned at t={i*10} with no emotion change - bug is back"
        )


def test_transition_command_shape_when_no_transition():
    orchestrator = TransitionOrchestrator()
    result = orchestrator.process_frame(timestamp=1.0, emotion="Calm", confidence=0.9)
    command = build_transition_command(result)
    assert command["should_transition"] is False
    assert command["type"] == "transition_command"


def test_transition_command_major_scale_on_downbeat():
    orchestrator = TransitionOrchestrator()
    for t in (1.0, 2.0, 3.0):
        orchestrator.process_frame(timestamp=t, emotion="Calm", confidence=0.90)
    orchestrator.process_frame(timestamp=4.0, emotion="Excited", confidence=0.93)
    result = orchestrator.process_frame(
        timestamp=5.0, emotion="Excited", confidence=0.93, beat=True, downbeat=True,
    )
    command = build_transition_command(result)

    assert command["should_transition"] is True
    assert command["transition_type"] == "major"
    assert command["target_emotion"] == "Excited"
    assert "duration_ms" in command
    assert "strength" in command
    assert "confidence" in command


def test_transition_command_minor_scale_on_plain_beat():
    orchestrator = TransitionOrchestrator()
    for t in (1.0, 2.0, 3.0):
        orchestrator.process_frame(timestamp=t, emotion="Calm", confidence=0.90)
    orchestrator.process_frame(timestamp=4.0, emotion="Happy", confidence=0.92)
    result = orchestrator.process_frame(
        timestamp=5.0, emotion="Happy", confidence=0.92, beat=True,
    )
    command = build_transition_command(result)

    assert command["transition_type"] == "minor"
