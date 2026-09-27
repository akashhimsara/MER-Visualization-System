from src.evaluation.metrics import (
    count_transitions,
    calculate_transition_frequency
)


results = [
    {"transition": False},
    {"transition": True},
    {"transition": False},
    {"transition": True},
]


assert count_transitions(results) == 2

assert calculate_transition_frequency(
    results,
    duration_seconds=10
) == 0.2

assert calculate_transition_frequency(
    results,
    duration_seconds=0
) == 0.0


print("Metrics tests passed!")