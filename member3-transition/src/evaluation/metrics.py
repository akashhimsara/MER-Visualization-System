def count_transitions(results):
    return sum(
        1 for result in results
        if result["transition"] is True
    )


def calculate_transition_frequency(results, duration_seconds):
    if duration_seconds <= 0:
        return 0.0

    transition_count = count_transitions(results)

    return round(transition_count / duration_seconds, 2)