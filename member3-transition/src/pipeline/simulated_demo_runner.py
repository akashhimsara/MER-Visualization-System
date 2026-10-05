"""
End-to-end presentation demo.

Simulated emotion stream + simulated musical structure
-> TransitionOrchestrator
-> TransitionCommand

Run with:
    python -m src.pipeline.simulated_demo_runner
"""
import joblib

from src.pipeline.orchestrator import TransitionOrchestrator
from src.pipeline.transition_command import build_transition_command
from src.simulator.structure_stream_simulator import (
    generate_structure_frame
)


EMOTION_SEGMENTS = [
    ("Calm", 0.0, 10.0),
    ("Happy", 10.0, 20.0),
    ("Excited", 20.0, 30.0),
    ("Sad", 30.0, 40.0),
]

FRAME_INTERVAL = 0.5
BPM = 120


def emotion_at(timestamp):
    for emotion, start, end in EMOTION_SEGMENTS:
        if start <= timestamp < end:
            return emotion

    return EMOTION_SEGMENTS[-1][0]


def run_demo():
    model = joblib.load("models/transition_model.pkl")
    orchestrator = TransitionOrchestrator(ml_model=model)

    duration = EMOTION_SEGMENTS[-1][2]

    timestamp = 0.0
    commands = []

    while timestamp < duration:

        emotion = emotion_at(timestamp)

        structure = generate_structure_frame(
            timestamp,
            bpm=BPM
        )

        result = orchestrator.process_frame(
            timestamp=timestamp,
            emotion=emotion,
            confidence=0.90,
            **structure
        )

        command = build_transition_command(result)

        if command["should_transition"]:
            commands.append(command)

            print(
                f"t={timestamp:5.1f}s -> "
                f"{command}"
            )

        timestamp += FRAME_INTERVAL

    print(
        f"\n{len(commands)} transition command(s) "
        f"generated over {duration}s of simulated audio."
    )

    return commands


if __name__ == "__main__":
    run_demo()