from src.pipeline.orchestrator import TransitionOrchestrator

TEST_FRAMES = [
    (1.0, "Happy", 0.90, True, False, False, False),
    (2.0, "Happy", 0.92, False, False, False, False),
    (3.0, "Sad", 0.88, True, True, False, True),
    (4.0, "Sad", 0.91, False, False, True, False),
    (9.0, "Excited", 0.95, True, False, True, True),
]


def test_orchestrator_produces_valid_results_for_every_frame():
    orchestrator = TransitionOrchestrator()

    for timestamp, emotion, confidence, beat, downbeat, onset, energy_change in TEST_FRAMES:
        result = orchestrator.process_frame(
            timestamp=timestamp, emotion=emotion, confidence=confidence,
            beat=beat, downbeat=downbeat, onset=onset, energy_change=energy_change,
        )
        assert result["score"] >= 0.0
        assert result["persistence"] >= 0.0
        assert isinstance(result["transition"], bool)