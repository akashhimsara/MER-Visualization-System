"""
Automated Test Suite for Milestone 6: User History & Preferences Layer.

Verifies:
- UserPersonalizationState initialization and metrics
- Per-preset statistics tracking and isolation
- Synchronization with AdaptivePersonalizationEngine
- Bounded recent histories for recommendations and feedback
- Duplicate and unmatched feedback protections
- Deterministic preference summaries and tie breaking
- Clean JSON serialization for future PostgreSQL persistence
- True instance isolation (no shared mutable state)
"""

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    AdaptivePersonalizationEngine,
    MOCK_ARM_PRESETS,
    PRESET_CALM_NEGATIVE,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_TENSE_NEGATIVE,
    PresetStats,
    UserPersonalizationState,
)

REC_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "recommendation.schema.json"
FB_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "feedback-event.schema.json"


@pytest.fixture(scope="module")
def rec_validator() -> Draft202012Validator:
    with open(REC_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


@pytest.fixture(scope="module")
def fb_validator() -> Draft202012Validator:
    with open(FB_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


def make_tier3(
    valence: float = 0.8,
    arousal: float = 0.8,
    session_id: str = "sess_user_01",
    sequence: int = 1,
    audio_time_ms: int = 1000,
) -> Dict[str, Any]:
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "emotion": {
            "valence": valence,
            "arousal": arousal,
            "confidence": None,
        },
    }


def make_feedback(
    feedback_type: str,
    preset_id: str,
    session_id: str = "sess_user_01",
    sequence: int = 1,
    audio_time_ms: int = 2000,
    feedback_id: str = "fb_u_01",
    rating: Optional[int] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"type": feedback_type}
    if rating is not None:
        payload["rating"] = rating
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms

    return {
        "schema_version": "1.1",
        "event_type": "feedback.event",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "feedback_id": feedback_id,
        "preset_id": preset_id,
        "feedback": payload,
    }


# 1. Clean user-state initialization
def test_clean_user_state_initialization():
    state = UserPersonalizationState(user_id="user-42", max_history_size=15)

    assert state.user_id == "user-42"
    assert state.max_history_size == 15
    assert state.recommendation_count == 0
    assert state.feedback_count == 0
    assert state.successful_learning_updates == 0
    assert state.last_recommended_preset is None
    assert state.last_feedback_type is None
    assert state.cumulative_reward == 0.0
    assert state.average_reward is None
    assert len(state.recent_recommendations) == 0
    assert len(state.recent_feedback) == 0

    # Preset stats initialized for all default mock arms with 0 counts and None averages
    for arm in MOCK_ARM_PRESETS:
        stats = state.get_preset_stats(arm)
        assert stats.preset_id == arm
        assert stats.recommendation_count == 0
        assert stats.feedback_count == 0
        assert stats.like_count == 0
        assert stats.dislike_count == 0
        assert stats.rating_count == 0
        assert stats.average_rating is None
        assert stats.average_reward is None
        assert stats.cumulative_reward == 0.0


# 2. Recommendation count increments correctly
# 3. Last recommended preset updates correctly
# 4. Per-preset recommendation counts remain isolated
def test_recommendation_count_and_preset_isolation():
    engine = AdaptivePersonalizationEngine(user_id="user-rec-test")
    state = engine.user_state

    # 1st rec: Q1 (valence >= 0, arousal >= 0) -> energetic_positive
    engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)
    assert state.recommendation_count == 1
    assert state.last_recommended_preset == PRESET_ENERGETIC_POSITIVE
    assert state.get_preset_stats(PRESET_ENERGETIC_POSITIVE).recommendation_count == 1
    assert state.get_preset_stats(PRESET_CALM_POSITIVE).recommendation_count == 0

    # 2nd rec: Q2 (valence >= 0, arousal < 0) -> calm_positive
    engine.recommend(make_tier3(0.5, -0.6), recommendation_sequence=2)
    assert state.recommendation_count == 2
    assert state.last_recommended_preset == PRESET_CALM_POSITIVE
    assert state.get_preset_stats(PRESET_ENERGETIC_POSITIVE).recommendation_count == 1
    assert state.get_preset_stats(PRESET_CALM_POSITIVE).recommendation_count == 1
    assert state.get_preset_stats(PRESET_TENSE_NEGATIVE).recommendation_count == 0

    # 3rd rec: Q1 -> energetic_positive again
    engine.recommend(make_tier3(0.9, 0.4), recommendation_sequence=3)
    assert state.recommendation_count == 3
    assert state.last_recommended_preset == PRESET_ENERGETIC_POSITIVE
    assert state.get_preset_stats(PRESET_ENERGETIC_POSITIVE).recommendation_count == 2
    assert state.get_preset_stats(PRESET_CALM_POSITIVE).recommendation_count == 1


# 5. Like feedback updates correct statistics
def test_like_feedback_updates_statistics():
    engine = AdaptivePersonalizationEngine(user_id="user-like")
    rec = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)

    fb = make_feedback("like", preset_id=rec["recommended_preset_id"], feedback_id="fb_like_01")
    res = engine.process_feedback(fb)
    assert res.applied is True

    state = engine.user_state
    assert state.feedback_count == 1
    assert state.last_feedback_type == "like"
    assert state.successful_learning_updates == 1
    assert state.cumulative_reward == 1.0
    assert state.average_reward == 1.0

    preset_stats = state.get_preset_stats(rec["recommended_preset_id"])
    assert preset_stats.feedback_count == 1
    assert preset_stats.like_count == 1
    assert preset_stats.cumulative_reward == 1.0
    assert preset_stats.average_reward == 1.0


# 6. Dislike feedback updates correct statistics
def test_dislike_feedback_updates_statistics():
    engine = AdaptivePersonalizationEngine(user_id="user-dislike")
    rec = engine.recommend(make_tier3(-0.8, -0.8), recommendation_sequence=1)
    arm = rec["recommended_preset_id"]
    assert arm == PRESET_CALM_NEGATIVE

    fb = make_feedback("dislike", preset_id=arm, feedback_id="fb_dislike_01")
    engine.process_feedback(fb)

    state = engine.user_state
    assert state.feedback_count == 1
    assert state.last_feedback_type == "dislike"
    assert state.successful_learning_updates == 1
    assert state.cumulative_reward == -1.0
    assert state.average_reward == -1.0

    preset_stats = state.get_preset_stats(arm)
    assert preset_stats.feedback_count == 1
    assert preset_stats.dislike_count == 1
    assert preset_stats.cumulative_reward == -1.0
    assert preset_stats.average_reward == -1.0


# 7. Ratings update rating aggregates correctly
def test_rating_aggregates_calculation():
    engine = AdaptivePersonalizationEngine(user_id="user-rating")

    # 1st interaction: rating 5 (reward = +1.0)
    rec1 = engine.recommend(make_tier3(0.7, 0.7), recommendation_sequence=1)
    engine.process_feedback(make_feedback("rating", rec1["recommended_preset_id"], rating=5, feedback_id="fb_r1"))

    # 2nd interaction: rating 3 (reward = 0.0)
    rec2 = engine.recommend(make_tier3(0.7, 0.7), recommendation_sequence=2)
    engine.process_feedback(make_feedback("rating", rec2["recommended_preset_id"], rating=3, feedback_id="fb_r2"))

    arm1 = rec1["recommended_preset_id"]
    stats1 = engine.user_state.get_preset_stats(arm1)
    assert stats1.rating_count >= 1
    assert stats1.average_rating is not None
    assert engine.user_state.feedback_count == 2
    assert engine.user_state.successful_learning_updates == 2
    # Ratings 5 and 3 produce rewards +1.0 and 0.0 -> cumulative 1.0, avg 0.5
    assert engine.user_state.cumulative_reward == 1.0
    assert engine.user_state.average_reward == 0.5


# 8. Preset select and preset skip counters update correctly
def test_preset_select_and_skip_counters():
    engine = AdaptivePersonalizationEngine(user_id="user-select-skip")

    # 1st recommendation and select
    rec1 = engine.recommend(make_tier3(0.5, -0.5), recommendation_sequence=1)
    res1 = engine.process_feedback(make_feedback("preset_select", rec1["recommended_preset_id"], feedback_id="fb_sel"))
    assert res1.applied is True

    # 2nd recommendation and skip
    rec2 = engine.recommend(make_tier3(0.5, -0.5), recommendation_sequence=2)
    res2 = engine.process_feedback(make_feedback("preset_skip", rec2["recommended_preset_id"], feedback_id="fb_skip"))
    assert res2.applied is True

    assert engine.user_state.feedback_count == 2
    assert engine.user_state.successful_learning_updates == 2

    stats1 = engine.user_state.get_preset_stats(rec1["recommended_preset_id"])
    assert stats1.preset_select_count == 1
    stats2 = engine.user_state.get_preset_stats(rec2["recommended_preset_id"])
    assert stats2.preset_skip_count == 1

    # Rewards: +0.75 + (-0.75) = 0.0
    assert engine.user_state.cumulative_reward == 0.0
    assert engine.user_state.average_reward == 0.0


# 9. Numerical rewards update cumulative and average reward correctly
def test_cumulative_and_average_rewards():
    engine = AdaptivePersonalizationEngine(user_id="user-rewards")

    # Sequence of 3 distinct feedbacks:
    # 1: like (+1.0)
    rec1 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)
    res1 = engine.process_feedback(make_feedback("like", rec1["recommended_preset_id"], feedback_id="fb_1"))
    assert res1.applied is True

    # 2: rating 4 (+0.5)
    rec2 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=2)
    res2 = engine.process_feedback(make_feedback("rating", rec2["recommended_preset_id"], rating=4, feedback_id="fb_2"))
    assert res2.applied is True

    # 3: dislike (-1.0)
    rec3 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=3)
    res3 = engine.process_feedback(make_feedback("dislike", rec3["recommended_preset_id"], feedback_id="fb_3"))
    assert res3.applied is True

    state = engine.user_state
    # Total cumulative: 1.0 + 0.5 - 1.0 = 0.5
    assert state.cumulative_reward == 0.5
    assert state.feedback_count == 3
    assert state.successful_learning_updates == 3
    # Average: 0.5 / 3 = 0.1667
    assert pytest.approx(state.average_reward, rel=1e-4) == 0.1667


# 10. View duration does not fabricate reward
def test_view_duration_does_not_fabricate_reward():
    engine = AdaptivePersonalizationEngine(user_id="user-vd")
    rec = engine.recommend(make_tier3(0.6, 0.6), recommendation_sequence=1)
    arm = rec["recommended_preset_id"]

    fb = make_feedback("view_duration", arm, duration_ms=45000, feedback_id="fb_vd")
    res = engine.process_feedback(fb)
    assert res.status == "auxiliary"

    state = engine.user_state
    assert state.feedback_count == 1
    assert state.last_feedback_type == "view_duration"
    assert state.successful_learning_updates == 0
    assert state.cumulative_reward == 0.0
    assert state.average_reward is None

    stats = state.get_preset_stats(arm)
    assert stats.feedback_count == 1
    assert stats.view_duration_count == 1
    assert stats.total_duration_ms == 45000
    assert stats.cumulative_reward == 0.0
    assert stats.average_reward is None


# 11. Duplicate feedback does not update user state twice
def test_duplicate_feedback_protection():
    engine = AdaptivePersonalizationEngine(user_id="user-dup")
    rec = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)
    fb = make_feedback("like", rec["recommended_preset_id"], feedback_id="fb_dup_01")

    # 1st processing succeeds
    res1 = engine.process_feedback(fb)
    assert res1.applied is True
    assert engine.user_state.feedback_count == 1
    assert engine.user_state.cumulative_reward == 1.0
    assert len(engine.user_state.recent_feedback) == 1

    # 2nd processing is duplicate
    res2 = engine.process_feedback(fb)
    assert res2.status == "duplicate"
    assert res2.applied is False

    # State must be completely unchanged
    assert engine.user_state.feedback_count == 1
    assert engine.user_state.cumulative_reward == 1.0
    assert engine.user_state.successful_learning_updates == 1
    assert len(engine.user_state.recent_feedback) == 1


# 12. Unmatched feedback does not corrupt state
def test_unmatched_feedback_does_not_corrupt_state():
    engine = AdaptivePersonalizationEngine(user_id="user-unmatched")
    state = engine.user_state

    fb_unmatched = make_feedback("like", "non-existent-preset", session_id="ghost_sess", feedback_id="fb_ghost")
    res = engine.process_feedback(fb_unmatched)
    assert res.status == "unmatched"
    assert res.applied is False

    assert state.feedback_count == 0
    assert state.cumulative_reward == 0.0
    assert state.successful_learning_updates == 0
    assert state.last_feedback_type is None
    assert len(state.recent_feedback) == 0


# 13. Recent recommendation history respects maximum length
def test_recent_recommendation_history_bounded():
    max_len = 5
    engine = AdaptivePersonalizationEngine(user_id="user-rec-bound", max_history_size=max_len)

    for i in range(12):
        engine.recommend(make_tier3(0.5, 0.5), recommendation_sequence=i + 1)

    state = engine.user_state
    assert state.recommendation_count == 12
    assert len(state.recent_recommendations) == max_len

    # Confirms the 5 most recent recommendations are kept (sequences 8 to 12)
    expected_sequences = [8, 9, 10, 11, 12]
    actual_sequences = [r["sequence"] for r in state.recent_recommendations]
    assert actual_sequences == expected_sequences


# 14. Recent feedback history respects maximum length
def test_recent_feedback_history_bounded():
    max_len = 4
    engine = AdaptivePersonalizationEngine(user_id="user-fb-bound", max_history_size=max_len)

    for i in range(8):
        rec = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=i + 1)
        fb = make_feedback("like", rec["recommended_preset_id"], feedback_id=f"fb_bound_{i}")
        res = engine.process_feedback(fb)
        assert res.applied is True

    state = engine.user_state
    assert state.feedback_count == 8
    assert len(state.recent_feedback) == max_len

    expected_fb_ids = [f"fb_bound_{i}" for i in range(4, 8)]
    actual_fb_ids = [f["feedback_id"] for f in state.recent_feedback]
    assert actual_fb_ids == expected_fb_ids


# 15. Deterministic preference-summary tie breaking
def test_deterministic_preference_summary_tie_breaking():
    state = UserPersonalizationState(user_id="user-tie-breaker")

    # Tie scenario:
    # Preset A (mock-calm-positive) and Preset B (mock-energetic-positive)
    # both receive 2 likes and +2.0 cumulative reward
    arm_a = PRESET_CALM_POSITIVE       # Alphabetically "mock-calm-positive"
    arm_b = PRESET_ENERGETIC_POSITIVE  # Alphabetically "mock-energetic-positive"

    for i in range(2):
        state.record_feedback("like", arm_a, "sess_1", reward=1.0, feedback_id=f"fb_a_{i}")
        state.record_feedback("like", arm_b, "sess_1", reward=1.0, feedback_id=f"fb_b_{i}")

    # Both have like_count == 2
    assert state.get_preset_stats(arm_a).like_count == 2
    assert state.get_preset_stats(arm_b).like_count == 2

    # Deterministic alphabetical tie-breaking: "mock-calm-positive" < "mock-energetic-positive"
    assert state.get_most_frequently_liked_preset() == PRESET_CALM_POSITIVE
    assert state.get_most_positively_rewarded_preset() == PRESET_CALM_POSITIVE

    # Now give arm_b a 3rd like -> arm_b unambiguously wins
    state.record_feedback("like", arm_b, "sess_1", reward=1.0, feedback_id="fb_b_win")
    assert state.get_most_frequently_liked_preset() == PRESET_ENERGETIC_POSITIVE
    assert state.get_most_positively_rewarded_preset() == PRESET_ENERGETIC_POSITIVE


# 16. to_dict() output is JSON serializable
def test_to_dict_json_serializable():
    engine = AdaptivePersonalizationEngine(user_id="user-json-test")
    rec1 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)
    engine.process_feedback(make_feedback("like", rec1["recommended_preset_id"], feedback_id="fb_json_1"))

    rec2 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=2)
    engine.process_feedback(make_feedback("view_duration", rec2["recommended_preset_id"], duration_ms=25000, feedback_id="fb_json_2"))

    d = engine.user_state.to_dict()
    # Must serialize without TypeError
    dumped = json.dumps(d)
    loaded = json.loads(dumped)

    assert loaded["user_id"] == "user-json-test"
    assert loaded["recommendation_count"] == 2
    assert loaded["feedback_count"] == 2
    assert loaded["successful_learning_updates"] == 1
    assert loaded["cumulative_reward"] == 1.0
    assert loaded["preference_summary"]["most_frequently_liked_preset"] == rec1["recommended_preset_id"]
    assert len(loaded["recent_recommendations"]) == 2
    assert len(loaded["recent_feedback"]) == 2


# 17. Two engine/user-state instances do not share mutable state
def test_state_isolation_between_instances():
    engine_1 = AdaptivePersonalizationEngine(user_id="user_alpha")
    engine_2 = AdaptivePersonalizationEngine(user_id="user_beta")

    assert engine_1.user_state is not engine_2.user_state
    assert engine_1.user_state.user_id != engine_2.user_state.user_id

    # Mutate engine_1
    rec = engine_1.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)
    engine_1.process_feedback(make_feedback("like", rec["recommended_preset_id"], feedback_id="fb_iso"))

    assert engine_1.user_state.recommendation_count == 1
    assert engine_1.user_state.feedback_count == 1
    assert engine_1.user_state.successful_learning_updates == 1

    # engine_2 must remain completely pristine
    assert engine_2.user_state.recommendation_count == 0
    assert engine_2.user_state.feedback_count == 0
    assert engine_2.user_state.successful_learning_updates == 0
    assert len(engine_2.user_state.recent_recommendations) == 0
    assert len(engine_2.user_state.recent_feedback) == 0


# 18. Successful learning update count stays consistent with adaptive engine state
def test_learning_update_count_stays_consistent():
    engine = AdaptivePersonalizationEngine(user_id="user-sync")
    arm = PRESET_ENERGETIC_POSITIVE

    assert engine.successful_update_count == 0
    assert engine.user_state.successful_learning_updates == 0

    # 1. Recommendation (no feedback yet)
    rec1 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=1)
    assert engine.successful_update_count == engine.user_state.successful_learning_updates == 0

    # 2. Auxiliary view_duration feedback (does not increment learning count)
    engine.process_feedback(make_feedback("view_duration", rec1["recommended_preset_id"], duration_ms=10000, feedback_id="fb_sync_vd"))
    assert engine.successful_update_count == engine.user_state.successful_learning_updates == 0

    # 3. Duplicate feedback (does not increment learning count)
    engine.process_feedback(make_feedback("view_duration", rec1["recommended_preset_id"], duration_ms=10000, feedback_id="fb_sync_vd"))
    assert engine.successful_update_count == engine.user_state.successful_learning_updates == 0

    # 4. Like feedback (increments learning count to 1)
    engine.process_feedback(make_feedback("like", rec1["recommended_preset_id"], feedback_id="fb_sync_like"))
    assert engine.successful_update_count == engine.user_state.successful_learning_updates == 1

    # 5. Another rec + dislike (increments learning count to 2)
    rec2 = engine.recommend(make_tier3(0.8, 0.8), recommendation_sequence=2)
    engine.process_feedback(make_feedback("dislike", rec2["recommended_preset_id"], feedback_id="fb_sync_dislike"))
    assert engine.successful_update_count == engine.user_state.successful_learning_updates == 2
