"""
Simulates musical structure signals (beat, downbeat, onset, energy_change)
for a given tempo.

Used to exercise the transition pipeline before real DEAM audio
structure extraction is added.
"""


def generate_structure_frame(timestamp, bpm=120, beat_tolerance=0.05):
    beat_interval = 60.0 / bpm
    position_in_beat = timestamp % beat_interval

    beat = (
        position_in_beat < beat_tolerance
        or (beat_interval - position_in_beat) < beat_tolerance
    )

    beat_index = round(timestamp / beat_interval)

    downbeat = beat and (beat_index % 4 == 0)

    onset = beat

    energy_change = downbeat

    return {
        "beat": beat,
        "downbeat": downbeat,
        "onset": onset,
        "energy_change": energy_change,
    }


def simulate_structure_stream(timestamps, bpm=120):
    return [
        generate_structure_frame(
            timestamp,
            bpm=bpm
        )
        for timestamp in timestamps
    ]