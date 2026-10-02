from src.pipeline.orchestrator import TransitionOrchestrator


orchestrator = TransitionOrchestrator()


frames = [
    (1.0, "Happy", 0.90, False, False, False, False),
    (2.0, "Happy", 0.91, False, False, False, False),
    (3.0, "Happy", 0.92, True, False, False, False),
    (4.0, "Happy", 0.90, False, False, False, False),

    (5.0, "Sad", 0.89, False, False, False, False),
    (6.0, "Sad", 0.90, False, False, False, False),
    (7.0, "Sad", 0.91, True, True, False, True),
    (8.0, "Sad", 0.92, False, False, False, False),
    (9.0, "Sad", 0.93, False, False, False, False),
    (10.0, "Sad", 0.94, True, False, True, True),
]


results = []

for frame in frames:
    (
        timestamp,
        emotion,
        confidence,
        beat,
        downbeat,
        onset,
        energy_change
    ) = frame

    result = orchestrator.process_frame(
        timestamp=timestamp,
        emotion=emotion,
        confidence=confidence,
        beat=beat,
        downbeat=downbeat,
        onset=onset,
        energy_change=energy_change
    )

    results.append(result)


emotion_changes = [
    result
    for result in results
    if result["emotion_changed"]
]


assert len(emotion_changes) > 0

print("Sustained emotion change test passed!")
print("Detected emotion changes:", len(emotion_changes))

for result in results:
    print(result)