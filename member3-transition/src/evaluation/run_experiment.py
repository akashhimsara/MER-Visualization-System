from src.pipeline.orchestrator import TransitionOrchestrator
from src.baselines.immediate_reactive import ImmediateReactiveBaseline
from src.baselines.fixed_rule_based import FixedRuleBasedBaseline
from src.evaluation.metrics import count_transitions


def run_proposed_system(test_frames):
    orchestrator = TransitionOrchestrator()

    results = []

    for frame in test_frames:
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

    return results


def run_immediate_reactive(test_frames):
    baseline = ImmediateReactiveBaseline()

    results = []
    previous_emotion = None

    for frame in test_frames:
        (
            timestamp,
            emotion,
            confidence,
            beat,
            downbeat,
            onset,
            energy_change
        ) = frame

        transition = baseline.should_transition(
            previous_emotion,
            emotion
        )

        results.append({
            "timestamp": timestamp,
            "transition": transition
        })

        previous_emotion = emotion

    return results


def run_fixed_rule_based(test_frames):
    baseline = FixedRuleBasedBaseline()

    results = []
    previous_emotion = None

    for frame in test_frames:
        (
            timestamp,
            emotion,
            confidence,
            beat,
            downbeat,
            onset,
            energy_change
        ) = frame

        emotion_changed = (
            previous_emotion is not None
            and previous_emotion != emotion
        )

        transition = baseline.should_transition(
            emotion_changed=emotion_changed,
            confidence=confidence,
            beat=beat,
            downbeat=downbeat
        )

        results.append({
            "timestamp": timestamp,
            "transition": transition
        })

        previous_emotion = emotion

    return results


if __name__ == "__main__":

    test_frames = [
        (1.0, "Happy", 0.90, True, False, False, False),
        (2.0, "Happy", 0.92, False, False, False, False),
        (3.0, "Sad", 0.88, True, True, False, True),
        (4.0, "Sad", 0.91, False, False, True, False),
        (9.0, "Excited", 0.95, True, False, True, True),
    ]

    proposed_results = run_proposed_system(test_frames)
    immediate_results = run_immediate_reactive(test_frames)
    fixed_results = run_fixed_rule_based(test_frames)

    print("\nProposed Adaptive:")
    for result in proposed_results:
        print(result)

    print("\nImmediate Reactive:")
    for result in immediate_results:
        print(result)

    print("\nFixed Rule-Based:")
    for result in fixed_results:
        print(result)

    print("\nTransition Counts:")

    print(
        "Proposed:",
        count_transitions(proposed_results)
    )

    print(
        "Immediate Reactive:",
        count_transitions(immediate_results)
    )

    print(
        "Fixed Rule-Based:",
        count_transitions(fixed_results)
    )