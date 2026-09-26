from src.pipeline.orchestrator import TransitionOrchestrator


orchestrator = TransitionOrchestrator()

test_frames = [
    (1.0, "Happy", 0.90, True, False, False, False),
    (2.0, "Happy", 0.92, False, False, False, False),
    (3.0, "Sad", 0.88, True, True, False, True),
    (4.0, "Sad", 0.91, False, False, True, False),
    (9.0, "Excited", 0.95, True, False, True, True),
]


for frame in test_frames:

    timestamp, emotion, confidence, beat, downbeat, onset, energy_change = frame

    result = orchestrator.process_frame(
        timestamp=timestamp,
        emotion=emotion,
        confidence=confidence,
        beat=beat,
        downbeat=downbeat,
        onset=onset,
        energy_change=energy_change
    )

    print(result)