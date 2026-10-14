"""
Automated Test Suite for Milestone 5: In-Memory Adaptive Personalization Learning Loop.

Verifies end-to-end integration:
MER Tier 3 -> Context Vector -> Cold-Start / LinUCB -> Recommendation Event
-> FeedbackEvent -> Reward -> LinUCB Model Update -> Future Recommendations Adapt.
"""

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    AdaptivePersonalizationEngine,
    FeedbackProcessingResult,
    LinUCB,
    MOCK_ARM_PRESETS,
    PRESET_CALM_NEGATIVE,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_TENSE_NEGATIVE,
    build_context_vector,
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


def make_tier3_event(
    valence: float = 0.8,
    arousal: float = 0.8,
    session_id: str = "sess_adaptive_001",
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


def make_feedback_event(
    feedback_type: str,
    preset_id: str = PRESET_ENERGETIC_POSITIVE,
    session_id: str = "sess_adaptive_001",
    sequence: int = 1,
    audio_time_ms: int = 2000,
    feedback_id: str = "fb_001",
    rating: Optional[int] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    fb_payload: Dict[str, Any] = {"type": feedback_type}
    if rating is not None:
        fb_payload["rating"] = rating
    if duration_ms is not None:
        fb_payload["duration_ms"] = duration_ms

    return {
        "schema_version": "1.1",
        "event_type": "feedback.event",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "feedback_id": feedback_id,
        "preset_id": preset_id,
        "feedback": fb_payload,
    }


def test_first_recommendation_uses_cold_start_and_null_score(rec_validator):
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(valence=0.7, arousal=0.7)

    rec = engine.recommend(tier3, recommendation_sequence=1)
    rec_validator.validate(rec)

    # 1. First recommendation uses strategy = cold_start
    assert rec["strategy"] == "cold_start"
    # 2. First recommendation has score = null
    assert rec["score"] is None
    assert rec["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE
    assert not engine.is_linucb_active


def test_recommendation_stores_correct_pending_context():
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(valence=0.45, arousal=-0.65, session_id="sess_context_test", audio_time_ms=5000)

    rec = engine.recommend(tier3, recommendation_sequence=10)

    assert len(engine.pending_interactions) == 1
    interaction = engine.pending_interactions[0]

    # 3. A recommendation stores the correct pending context
    assert interaction["session_id"] == "sess_context_test"
    assert interaction["recommendation_id"] == rec["recommendation_id"]
    assert interaction["recommended_preset_id"] == PRESET_CALM_POSITIVE
    assert interaction["audio_time_ms"] == 5000
    assert interaction["context_vector"] == [0.45, -0.65, 1.0]
    assert interaction["feedback_applied"] is False


def test_like_feedback_updates_correct_linucb_arm(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine(alpha=0.5)
    tier3 = make_tier3_event(valence=0.8, arousal=0.8, session_id="sess_like_test")
    rec = engine.recommend(tier3, recommendation_sequence=1)
    rec_validator.validate(rec)

    arm = rec["recommended_preset_id"]
    np.testing.assert_array_equal(engine.model.b[arm], np.zeros(3))

    fb = make_feedback_event(
        feedback_type="like",
        preset_id=arm,
        session_id="sess_like_test",
        feedback_id="fb_like_test_01",
    )
    fb_validator.validate(fb)

    # 4. Valid like feedback produces reward +1.0 and updates the correct LinUCB arm
    res = engine.process_feedback(fb)
    assert res.status == "applied"
    assert res.applied is True
    assert res.reward == 1.0
    assert res.arm_updated == arm
    assert engine.successful_update_count == 1
    assert engine.pending_interactions[0]["feedback_applied"] is True

    # b_a should have been updated by 1.0 * [0.8, 0.8, 1.0]
    expected_b = np.array([0.8, 0.8, 1.0], dtype=np.float64)
    np.testing.assert_allclose(engine.model.b[arm], expected_b)


def test_dislike_feedback_updates_arm_negatively(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine(alpha=0.5)
    tier3 = make_tier3_event(valence=-0.5, arousal=-0.5, session_id="sess_dislike_test")
    rec = engine.recommend(tier3, recommendation_sequence=1)
    rec_validator.validate(rec)

    arm = rec["recommended_preset_id"]
    assert arm == PRESET_CALM_NEGATIVE

    fb = make_feedback_event(
        feedback_type="dislike",
        preset_id=arm,
        session_id="sess_dislike_test",
        feedback_id="fb_dislike_test_01",
    )
    fb_validator.validate(fb)

    # 5. A dislike/negative feedback updates the correct arm negatively
    res = engine.process_feedback(fb)
    assert res.status == "applied"
    assert res.applied is True
    assert res.reward == -1.0
    assert res.arm_updated == arm

    expected_b = np.array([-1.0 * (-0.5), -1.0 * (-0.5), -1.0 * 1.0], dtype=np.float64)
    np.testing.assert_allclose(engine.model.b[arm], expected_b)


def test_transition_to_linucb_after_first_reward_update(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(valence=0.9, arousal=0.9, session_id="sess_trans")

    # Recommendation 1: before reward -> cold_start
    rec1 = engine.recommend(tier3, recommendation_sequence=1)
    assert rec1["strategy"] == "cold_start"
    assert rec1["score"] is None

    # Apply reward
    fb = make_feedback_event("like", preset_id=rec1["recommended_preset_id"], session_id="sess_trans")
    fb_validator.validate(fb)
    res = engine.process_feedback(fb)
    assert res.applied is True

    # 6. After the first successful reward update, the next recommendation uses strategy = linucb
    # 7. LinUCB recommendation contains a non-null score
    rec2 = engine.recommend(tier3, recommendation_sequence=2)
    rec_validator.validate(rec2)
    assert rec2["strategy"] == "linucb"
    assert isinstance(rec2["score"], float)
    assert engine.is_linucb_active


def test_schema_conformance_and_envelope_preservation(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(valence=0.3, arousal=-0.7, session_id="sess_env_01", audio_time_ms=12345)

    # 8. Recommendation output always validates against recommendation.schema.json
    rec1 = engine.recommend(tier3, recommendation_sequence=42)
    rec_validator.validate(rec1)

    # 10. session_id is preserved
    assert rec1["session_id"] == "sess_env_01"
    # 11. audio_time_ms is preserved
    assert rec1["audio_time_ms"] == 12345
    assert rec1["sequence"] == 42
    assert rec1["schema_version"] == "1.1"
    assert rec1["event_type"] == "personalization.recommendation"

    # 9. Feedback fixtures validate against feedback-event.schema.json
    fb = make_feedback_event("rating", preset_id=rec1["recommended_preset_id"], session_id="sess_env_01", rating=5)
    fb_validator.validate(fb)
    res = engine.process_feedback(fb)
    assert res.applied is True

    rec2 = engine.recommend(tier3, recommendation_sequence=43)
    rec_validator.validate(rec2)
    assert rec2["session_id"] == "sess_env_01"
    assert rec2["audio_time_ms"] == 12345
    assert rec2["sequence"] == 43


def test_view_duration_does_not_update_linucb_or_transition(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(session_id="sess_vd")

    rec = engine.recommend(tier3, recommendation_sequence=1)
    rec_validator.validate(rec)

    fb_view = make_feedback_event(
        "view_duration",
        preset_id=rec["recommended_preset_id"],
        session_id="sess_vd",
        duration_ms=45000,
        feedback_id="fb_vd_01",
    )
    fb_validator.validate(fb_view)

    # 12. view_duration with reward=None does NOT update LinUCB
    res = engine.process_feedback(fb_view)
    assert res.status == "auxiliary"
    assert res.applied is False
    assert res.reward is None
    assert engine.successful_update_count == 0

    # Model parameters remain at initialization
    arm = rec["recommended_preset_id"]
    np.testing.assert_array_equal(engine.model.A[arm], np.identity(3))
    np.testing.assert_array_equal(engine.model.b[arm], np.zeros(3))

    # 13. view_duration does NOT trigger transition from cold_start to linucb
    assert not engine.is_linucb_active
    next_rec = engine.recommend(tier3, recommendation_sequence=2)
    assert next_rec["strategy"] == "cold_start"
    assert next_rec["score"] is None


def test_duplicate_feedback_id_rejected_cleanly(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(session_id="sess_dup")
    rec = engine.recommend(tier3, recommendation_sequence=1)

    fb = make_feedback_event("like", preset_id=rec["recommended_preset_id"], session_id="sess_dup", feedback_id="fb_dup_01")
    fb_validator.validate(fb)

    # First submission succeeds
    res1 = engine.process_feedback(fb)
    assert res1.status == "applied"
    assert res1.applied is True
    assert engine.successful_update_count == 1

    arm = rec["recommended_preset_id"]
    b_after_first = copy.deepcopy(engine.model.b[arm])

    # 14. duplicate feedback_id does NOT update the model twice
    res2 = engine.process_feedback(fb)
    assert res2.status == "duplicate"
    assert res2.applied is False
    assert engine.successful_update_count == 1
    np.testing.assert_array_equal(engine.model.b[arm], b_after_first)

    # Strict mode raises ValueError
    with pytest.raises(ValueError, match="Duplicate feedback_id 'fb_dup_01'"):
        engine.process_feedback(fb, strict=True)


def test_unmatched_feedback_handled_cleanly(fb_validator):
    engine = AdaptivePersonalizationEngine()

    fb_unmatched_1 = make_feedback_event(
        "like",
        preset_id="mock-calm-positive",
        session_id="ghost_session",
        feedback_id="fb_ghost_01",
    )
    fb_validator.validate(fb_unmatched_1)

    # 15. feedback for a preset/session with no pending matching recommendation is rejected/handled cleanly
    res = engine.process_feedback(fb_unmatched_1)
    assert res.status == "unmatched"
    assert res.applied is False
    assert engine.successful_update_count == 0

    fb_unmatched_2 = make_feedback_event(
        "like",
        preset_id="mock-calm-positive",
        session_id="ghost_session",
        feedback_id="fb_ghost_02",
    )
    with pytest.raises(KeyError, match="No pending unprocessed recommendation found"):
        engine.process_feedback(fb_unmatched_2, strict=True)


def test_feedback_updates_only_matching_arm(rec_validator, fb_validator):
    engine = AdaptivePersonalizationEngine()
    tier3 = make_tier3_event(session_id="sess_iso")
    rec = engine.recommend(tier3, recommendation_sequence=1)

    updated_arm = rec["recommended_preset_id"]
    other_arms = [a for a in engine.arms if a != updated_arm]

    fb = make_feedback_event("like", preset_id=updated_arm, session_id="sess_iso")
    engine.process_feedback(fb)

    # 16. one feedback item updates only the matching arm
    for other in other_arms:
        np.testing.assert_array_equal(engine.model.A[other], np.identity(3))
        np.testing.assert_array_equal(engine.model.b[other], np.zeros(3))


def test_deterministic_identical_runs(rec_validator, fb_validator):
    # 17. same sequence of recommendations and feedback produces deterministic model state and deterministic future selections
    engine_a = AdaptivePersonalizationEngine(alpha=0.5)
    engine_b = AdaptivePersonalizationEngine(alpha=0.5)

    events = [
        make_tier3_event(0.8, 0.8, session_id="sess_det", sequence=1),
        make_tier3_event(-0.4, 0.6, session_id="sess_det", sequence=2),
        make_tier3_event(0.1, -0.9, session_id="sess_det", sequence=3),
    ]

    for idx, t3 in enumerate(events):
        rec_a = engine_a.recommend(t3, recommendation_sequence=idx + 1)
        rec_b = engine_b.recommend(t3, recommendation_sequence=idx + 1)
        assert rec_a == rec_b

        # Send feedback for the recommendation
        fb = make_feedback_event(
            feedback_type="like" if idx % 2 == 0 else "rating",
            rating=4 if idx % 2 != 0 else None,
            preset_id=rec_a["recommended_preset_id"],
            session_id="sess_det",
            feedback_id=f"fb_det_{idx}",
        )
        res_a = engine_a.process_feedback(fb)
        res_b = engine_b.process_feedback(fb)
        assert res_a == res_b

    # Verify model parameters are bitwise identical
    for arm in engine_a.arms:
        np.testing.assert_array_equal(engine_a.model.A[arm], engine_b.model.A[arm])
        np.testing.assert_array_equal(engine_a.model.b[arm], engine_b.model.b[arm])

    # Future recommendation is also identical
    test_eval = make_tier3_event(0.5, 0.5, session_id="sess_det", sequence=10)
    future_a = engine_a.recommend(test_eval, recommendation_sequence=10)
    future_b = engine_b.recommend(test_eval, recommendation_sequence=10)
    assert future_a == future_b


def test_repeated_positive_feedback_reinforces_arm_selection(rec_validator, fb_validator):
    # 18. repeated positive feedback in a matching context causes future LinUCB recommendations
    # to prefer the reinforced preset when mathematically expected
    engine = AdaptivePersonalizationEngine(alpha=0.2)
    tier3 = make_tier3_event(valence=0.85, arousal=0.85, session_id="sess_reinforce")

    # Step 1: Initial cold-start recommendation
    rec1 = engine.recommend(tier3, recommendation_sequence=1)
    rec_validator.validate(rec1)
    assert rec1["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE

    # Step 2: Reinforce energetic_positive with 5 positive feedbacks
    for i in range(5):
        # Generate rec so interaction is recorded
        r = engine.recommend(tier3, recommendation_sequence=i + 2)
        fb = make_feedback_event(
            feedback_type="like",
            preset_id=PRESET_ENERGETIC_POSITIVE,
            session_id="sess_reinforce",
            sequence=i + 1,
            feedback_id=f"fb_reinforce_{i}",
        )
        fb_validator.validate(fb)
        res = engine.process_feedback(fb)
        assert res.applied is True

    # Step 3: Now evaluate future recommendation in the same high valence/arousal context
    rec_future = engine.recommend(tier3, recommendation_sequence=10)
    rec_validator.validate(rec_future)

    assert rec_future["strategy"] == "linucb"
    assert rec_future["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE
    assert isinstance(rec_future["score"], float)
    assert rec_future["score"] > 0.95
