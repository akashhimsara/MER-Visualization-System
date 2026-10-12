from src.ml.build_deam_training_set import (
    FEATURE_COLUMNS,
    LOOKAHEAD_FRAMES,
    build_rows_for_song,
    confidence_proxy,
)


def _frames(*segments):
    """segments: (valence, arousal, number_of_frames). DEAM frames are 0.5 s apart."""
    frames = []
    timestamp_ms = 15000
    for valence, arousal, count in segments:
        for _ in range(count):
            frames.append({
                "song_id": 1,
                "timestamp_ms": timestamp_ms,
                "valence": valence,
                "arousal": arousal,
            })
            timestamp_ms += 500
    return frames


CALM = (0.5, -0.5)
EXCITED = (0.5, 0.5)


def test_confidence_proxy_is_low_on_a_boundary_and_high_inside_a_quadrant():
    assert confidence_proxy(0.0, 0.5) == 0.5
    assert confidence_proxy(0.5, -0.5) == 1.0
    assert confidence_proxy(0.1, 0.5) < confidence_proxy(0.2, 0.5)


def test_sustained_change_gets_label_1():
    rows = build_rows_for_song(1, _frames((*CALM, 12), (*EXCITED, 12)))
    assert len(rows) == 1
    assert rows[0]["label"] == 1


def test_flicker_that_reverts_gets_label_0():
    rows = build_rows_for_song(1, _frames((*CALM, 10), (*EXCITED, 2), (*CALM, 10)))
    assert rows[0]["label"] == 0


def test_change_too_close_to_the_end_of_the_clip_is_skipped():
    rows = build_rows_for_song(1, _frames((*CALM, 10), (*EXCITED, 4)))
    assert rows == []


def test_every_row_has_the_features_the_decider_expects_and_a_label():
    rows = build_rows_for_song(1, _frames((*CALM, 12), (*EXCITED, 12)))
    for column in FEATURE_COLUMNS + ["label", "song_id", "timestamp_s"]:
        assert column in rows[0]


def test_same_input_gives_same_rows_so_results_are_reproducible():
    frames = _frames((*CALM, 12), (*EXCITED, 12))
    assert build_rows_for_song(1, frames) == build_rows_for_song(1, frames)


def test_lookahead_is_three_seconds():
    assert LOOKAHEAD_FRAMES * 0.5 == 3.0