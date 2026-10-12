import numpy as np

from src.ml.train_on_deam import (
    cross_validate,
    make_logistic_regression,
    summarise,
)


def test_summarise_blocked_and_allowed_transitions():
    y = np.array([1, 1, 0, 0])
    predictions = np.array([1, 0, 1, 0])
    result = summarise(y, predictions)

    assert result["transitions_allowed"] == 2
    assert result["unnecessary_transition_rate"] == 0.5   # 1 of 2 allowed was flicker
    assert result["missed_genuine_rate"] == 0.5           # 1 of 2 genuine was blocked


def test_allow_everything_baseline_has_flicker_rate_of_one_minus_positive_share():
    y = np.array([1, 1, 1, 0])
    result = summarise(y, np.ones(4, dtype=int))
    assert result["unnecessary_transition_rate"] == 0.25
    assert result["missed_genuine_rate"] == 0.0


def test_blocking_everything_does_not_crash():
    y = np.array([1, 0, 1, 0])
    result = summarise(y, np.zeros(4, dtype=int))
    assert result["transitions_allowed"] == 0
    assert result["unnecessary_transition_rate"] == 0.0


def test_cross_validation_is_split_by_song_and_covers_every_row():
    rng = np.random.default_rng(0)
    songs = 30
    X = rng.random((songs * 4, 6))
    y = np.tile([0, 1, 0, 1], songs)
    groups = np.repeat(np.arange(songs), 4)

    # cross_validate asserts internally that no song appears in both train and test
    predictions, probabilities = cross_validate(
        make_logistic_regression, X, y, groups, folds=5
    )

    assert len(predictions) == len(y)
    assert len(probabilities) == len(y)
    assert set(predictions).issubset({0, 1})