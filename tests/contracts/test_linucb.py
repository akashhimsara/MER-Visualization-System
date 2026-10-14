import sys
import copy
import pytest
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    LinUCB,
    LinUCBSelection,
    MOCK_ARM_PRESETS,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_CALM_POSITIVE,
    PRESET_TENSE_NEGATIVE,
    PRESET_CALM_NEGATIVE,
    build_context_vector,
)


def test_initialization():
    arms = list(MOCK_ARM_PRESETS)
    d = 3
    alpha = 1.0

    model = LinUCB(arms=arms, context_dimension=d, alpha=alpha)

    assert model.arms == arms
    assert model.context_dimension == d
    assert model.alpha == alpha

    # 1. One A matrix per arm, shape (d, d), initialized as identity
    # 2. One b vector per arm, shape (d,), initialized as zeros
    for arm in arms:
        assert arm in model.A
        assert arm in model.b

        A_a = model.A[arm]
        b_a = model.b[arm]

        assert isinstance(A_a, np.ndarray)
        assert isinstance(b_a, np.ndarray)

        assert A_a.shape == (d, d)
        assert b_a.shape == (d,)

        np.testing.assert_array_equal(A_a, np.identity(d))
        np.testing.assert_array_equal(b_a, np.zeros(d))


def test_context_dimension_handling():
    arms = ["arm_a", "arm_b"]
    model = LinUCB(arms=arms, context_dimension=4, alpha=1.0)
    assert model.context_dimension == 4

    # Valid 4D context
    res = model.select_arm([0.1, 0.2, 0.3, 1.0])
    assert res.selected_arm == "arm_a"

    # Invalid dimension context
    with pytest.raises(ValueError, match="Expected 1D context vector of dimension 4"):
        model.select_arm([0.1, 0.2, 1.0])

    # Non-positive dimension in constructor
    with pytest.raises(ValueError, match="context_dimension must be a positive integer"):
        LinUCB(arms=arms, context_dimension=0)

    # Empty arms list
    with pytest.raises(ValueError, match="LinUCB requires at least one arm"):
        LinUCB(arms=[])

    # Negative alpha
    with pytest.raises(ValueError, match="alpha exploration parameter must be non-negative"):
        LinUCB(arms=arms, alpha=-0.5)


def test_initial_arm_scores_equal_without_learning():
    arms = list(MOCK_ARM_PRESETS)
    model = LinUCB(arms=arms, context_dimension=3, alpha=1.0)
    context = [0.65, -0.20, 1.0]

    selection = model.select_arm(context)

    # All initial exploitation scores are 0.0
    for arm in arms:
        assert selection.exploitation_scores[arm] == 0.0

    # All initial exploration scores and total scores are exactly identical
    scores = list(selection.arm_scores.values())
    assert len(scores) == len(arms)
    for s in scores:
        assert pytest.approx(s, rel=1e-9) == scores[0]


def test_deterministic_tie_breaking():
    arms = ["first_arm", "second_arm", "third_arm", "fourth_arm"]
    model = LinUCB(arms=arms, context_dimension=3, alpha=1.0)
    context = [0.5, 0.5, 1.0]

    # At initialization all scores are equal -> first arm must be selected
    selection = model.select_arm(context)
    assert selection.selected_arm == "first_arm"

    # Reordered arms -> new first arm must be selected
    reversed_arms = list(reversed(arms))
    model_rev = LinUCB(arms=reversed_arms, context_dimension=3, alpha=1.0)
    selection_rev = model_rev.select_arm(context)
    assert selection_rev.selected_arm == "fourth_arm"


def test_select_arm_does_not_modify_model_state():
    arms = list(MOCK_ARM_PRESETS)
    model = LinUCB(arms=arms, context_dimension=3, alpha=1.0)
    context = [0.7, -0.1, 1.0]

    # Snapshot initial state
    initial_A = {arm: model.A[arm].copy() for arm in arms}
    initial_b = {arm: model.b[arm].copy() for arm in arms}

    # Query multiple times
    for _ in range(5):
        model.select_arm(context)

    # Verify no state changes occurred
    for arm in arms:
        np.testing.assert_array_equal(model.A[arm], initial_A[arm])
        np.testing.assert_array_equal(model.b[arm], initial_b[arm])


def test_update_changes_only_selected_arm():
    arms = list(MOCK_ARM_PRESETS)
    model = LinUCB(arms=arms, context_dimension=3, alpha=1.0)
    context = [0.8, 0.8, 1.0]

    initial_A = {arm: model.A[arm].copy() for arm in arms}
    initial_b = {arm: model.b[arm].copy() for arm in arms}

    chosen_arm = PRESET_ENERGETIC_POSITIVE
    model.update(chosen_arm, context, reward=1.0)

    # Chosen arm must be updated
    assert not np.array_equal(model.A[chosen_arm], initial_A[chosen_arm])
    assert not np.array_equal(model.b[chosen_arm], initial_b[chosen_arm])

    # Expected exact mathematical values:
    x = np.array(context)
    expected_A = initial_A[chosen_arm] + np.outer(x, x)
    expected_b = initial_b[chosen_arm] + 1.0 * x

    np.testing.assert_array_almost_equal(model.A[chosen_arm], expected_A)
    np.testing.assert_array_almost_equal(model.b[chosen_arm], expected_b)

    # All other arms must remain strictly untouched
    for arm in arms:
        if arm != chosen_arm:
            np.testing.assert_array_equal(model.A[arm], initial_A[arm])
            np.testing.assert_array_equal(model.b[arm], initial_b[arm])


def test_positive_reward_increases_preference():
    arms = [PRESET_ENERGETIC_POSITIVE, PRESET_CALM_POSITIVE]
    # Use alpha=0.2 so exploitation dominates over initial uncertainty bonus
    model = LinUCB(arms=arms, context_dimension=3, alpha=0.2)
    context = [0.8, 0.8, 1.0]

    # Before update, both exploitation scores are 0.0
    initial_sel = model.select_arm(context)
    assert initial_sel.exploitation_scores[PRESET_ENERGETIC_POSITIVE] == 0.0

    # Repeated positive updates for energetic_positive
    for _ in range(5):
        model.update(PRESET_ENERGETIC_POSITIVE, context, reward=1.0)

    after_sel = model.select_arm(context)
    assert after_sel.selected_arm == PRESET_ENERGETIC_POSITIVE
    assert after_sel.exploitation_scores[PRESET_ENERGETIC_POSITIVE] > 0.0
    assert (
        after_sel.arm_scores[PRESET_ENERGETIC_POSITIVE]
        > after_sel.arm_scores[PRESET_CALM_POSITIVE]
    )


def test_negative_reward_reduces_preference():
    # If both arms are explored equally, positive vs negative reward determines preference
    arms = ["arm_pos", "arm_neg"]
    model = LinUCB(arms=arms, context_dimension=3, alpha=1.0)
    context = [0.5, 0.5, 1.0]

    for _ in range(3):
        model.update("arm_pos", context, reward=1.0)
        model.update("arm_neg", context, reward=-1.0)

    sel = model.select_arm(context)
    assert sel.selected_arm == "arm_pos"
    assert sel.arm_scores["arm_pos"] > sel.arm_scores["arm_neg"]
    assert sel.exploitation_scores["arm_pos"] > 0
    assert sel.exploitation_scores["arm_neg"] < 0


def test_context_sensitivity_not_popularity_counter():
    """
    Demonstrate that LinUCB ranks arms conditionally based on context (valence/arousal),
    rather than acting as a context-free global popularity counter.
    """
    arms = [PRESET_ENERGETIC_POSITIVE, PRESET_CALM_NEGATIVE]
    model = LinUCB(arms=arms, context_dimension=3, alpha=0.2)

    context_high = [0.9, 0.9, 1.0]    # High valence & high arousal
    context_low = [-0.9, -0.9, 1.0]   # Low valence & low arousal

    # Train energetic_positive on context_high with positive reward
    for _ in range(5):
        model.update(PRESET_ENERGETIC_POSITIVE, context_high, reward=1.0)

    # Train calm_negative on context_low with positive reward
    for _ in range(5):
        model.update(PRESET_CALM_NEGATIVE, context_low, reward=1.0)

    # In high emotion context -> model should select energetic_positive
    sel_high = model.select_arm(context_high)
    assert sel_high.selected_arm == PRESET_ENERGETIC_POSITIVE

    # In low emotion context -> model should select calm_negative
    sel_low = model.select_arm(context_low)
    assert sel_low.selected_arm == PRESET_CALM_NEGATIVE


def test_alpha_scales_exploration_contribution():
    arms = ["arm_1", "arm_2"]
    context = [0.6, -0.2, 1.0]

    model_zero = LinUCB(arms=arms, context_dimension=3, alpha=0.0)
    model_high = LinUCB(arms=arms, context_dimension=3, alpha=2.5)

    sel_zero = model_zero.select_arm(context)
    sel_high = model_high.select_arm(context)

    # Alpha 0 has zero exploration
    assert sel_zero.exploration_scores["arm_1"] == 0.0
    assert sel_zero.selected_score == 0.0  # (0 exploit + 0 explore initially)

    # Alpha 2.5 has non-zero exploration exactly 2.5 * base uncertainty
    base_uncertainty = np.linalg.norm(context)
    expected_explore = 2.5 * base_uncertainty
    assert pytest.approx(sel_high.exploration_scores["arm_1"], rel=1e-5) == expected_explore


def test_unknown_arm_rejected_cleanly():
    model = LinUCB(arms=["arm_1", "arm_2"], context_dimension=3)
    with pytest.raises(ValueError, match="Unknown arm_id 'unknown_arm'"):
        model.update("unknown_arm", [0.5, 0.5, 1.0], reward=1.0)


def test_invalid_context_dimensions_rejected():
    model = LinUCB(arms=["arm_1"], context_dimension=3)

    # Wrong dimension in select_arm
    with pytest.raises(ValueError, match="Expected 1D context vector of dimension 3"):
        model.select_arm([1.0, 2.0])

    # Wrong dimension in update
    with pytest.raises(ValueError, match="Expected 1D context vector of dimension 3"):
        model.update("arm_1", [1.0, 2.0, 3.0, 4.0], reward=1.0)


def test_determinism_across_identical_runs():
    arms = list(MOCK_ARM_PRESETS)
    model_a = LinUCB(arms=arms, context_dimension=3, alpha=0.8)
    model_b = LinUCB(arms=arms, context_dimension=3, alpha=0.8)

    contexts = [
        [0.8, 0.8, 1.0],
        [-0.5, 0.5, 1.0],
        [0.2, -0.7, 1.0],
    ]

    for ctx in contexts:
        sel_a = model_a.select_arm(ctx)
        sel_b = model_b.select_arm(ctx)

        assert sel_a == sel_b
        assert sel_a.selected_arm == sel_b.selected_arm
        assert sel_a.selected_score == sel_b.selected_score
        assert sel_a.arm_scores == sel_b.arm_scores

        model_a.update(sel_a.selected_arm, ctx, reward=0.75)
        model_b.update(sel_b.selected_arm, ctx, reward=0.75)

    # Verify final models are completely identical
    for arm in arms:
        np.testing.assert_array_equal(model_a.A[arm], model_b.A[arm])
        np.testing.assert_array_equal(model_a.b[arm], model_b.b[arm])


def test_integration_with_context_vector_builder():
    """Verify LinUCB directly consumes ContextVector objects from Milestone 3."""
    tier3_event = {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": "sess_linucb_001",
        "sequence": 1,
        "audio_time_ms": 1000,
        "emotion": {
            "valence": 0.75,
            "arousal": 0.60,
            "confidence": None,
        },
    }

    ctx_obj = build_context_vector(tier3_event)
    assert ctx_obj.dimension == 3

    model = LinUCB(arms=list(MOCK_ARM_PRESETS), context_dimension=3, alpha=0.5)

    # select_arm accepts ContextVector directly
    selection = model.select_arm(ctx_obj)
    assert selection.selected_arm == MOCK_ARM_PRESETS[0]

    # update accepts ContextVector directly
    model.update(selection.selected_arm, ctx_obj, reward=1.0)
    assert model.b[selection.selected_arm][0] == 0.75
    assert model.b[selection.selected_arm][1] == 0.60
    assert model.b[selection.selected_arm][2] == 1.0
