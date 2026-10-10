from src.evaluation.metrics import count_transitions, calculate_transition_frequency

RESULTS = [
    {"transition": False},
    {"transition": True},
    {"transition": False},
    {"transition": True},
]


def test_count_transitions():
    assert count_transitions(RESULTS) == 2


def test_calculate_transition_frequency():
    assert calculate_transition_frequency(RESULTS, duration_seconds=10) == 0.2


def test_calculate_transition_frequency_zero_duration():
    assert calculate_transition_frequency(RESULTS, duration_seconds=0) == 0.0