"""
Automated Test Suite for Milestone 7: PostgreSQL Persistence Layer.

Tests:
- Serializer/deserializer unit round-trips (LinUCB matrices, user states, presets).
- Dimension and shape validation (rejection of corrupted matrices/vectors).
- JSON compliance without unsafe pickle or bare NumPy types.
- PersonalizationRepository contract (tested via in-memory SQLite for CI/isolation).
- Multi-user and multi-arm isolation.
- Idempotency of processed feedback IDs.
- Full AdaptivePersonalizationEngine restore round-trip.
- Conditional live PostgreSQL integration check (skipped cleanly if no live PG available).
"""

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    AdaptivePersonalizationEngine,
    Base,
    LinUCB,
    MOCK_ARM_PRESETS,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    PersonalizationRepository,
    PresetStats,
    UserPersonalizationState,
    build_context_vector,
    deserialize_linucb_arm,
    deserialize_linucb_model,
    deserialize_user_state,
    generate_recommendation_id,
    persist_adaptive_engine,
    restore_adaptive_engine,
    sanitize_for_json,
    serialize_linucb_arm,
    serialize_linucb_model,
    serialize_user_state,
)


@pytest.fixture
def in_memory_repo() -> PersonalizationRepository:
    """Fixture providing a PersonalizationRepository backed by an isolated in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return PersonalizationRepository(session_factory=session_factory)


# 1. User state serialization/deserialization round-trip
def test_user_state_serialization_round_trip():
    state = UserPersonalizationState(user_id="user-rt-01", max_history_size=10)
    state.recommendation_count = 5
    state.feedback_count = 3
    state.successful_learning_updates = 2
    state.last_recommended_preset = PRESET_ENERGETIC_POSITIVE
    state.last_feedback_type = "like"
    state.cumulative_reward = 2.0
    state.numerical_reward_count = 2

    serialized = serialize_user_state(state)
    assert isinstance(serialized, dict)

    restored = deserialize_user_state(serialized)
    assert restored.user_id == state.user_id
    assert restored.recommendation_count == 5
    assert restored.feedback_count == 3
    assert restored.successful_learning_updates == 2
    assert restored.last_recommended_preset == PRESET_ENERGETIC_POSITIVE
    assert restored.last_feedback_type == "like"
    assert restored.cumulative_reward == 2.0
    assert restored.average_reward == 1.0


# 2. Per-preset statistics round-trip
def test_preset_statistics_round_trip():
    stats = PresetStats("mock-calm-positive")
    stats.recommendation_count = 4
    stats.feedback_count = 3
    stats.like_count = 1
    stats.dislike_count = 0
    stats.rating_count = 2
    stats.rating_sum = 8.0  # avg = 4.0
    stats.preset_select_count = 1
    stats.preset_skip_count = 0
    stats.cumulative_reward = 1.75
    stats.numerical_reward_count = 2
    stats.view_duration_count = 1
    stats.total_duration_ms = 35000

    d = stats.to_dict()
    restored = PresetStats.from_dict(d)

    assert restored.preset_id == "mock-calm-positive"
    assert restored.recommendation_count == 4
    assert restored.feedback_count == 3
    assert restored.like_count == 1
    assert restored.rating_count == 2
    assert restored.average_rating == 4.0
    assert restored.preset_select_count == 1
    assert restored.cumulative_reward == 1.75
    assert restored.average_reward == round(1.75 / 2, 4)
    assert restored.view_duration_count == 1
    assert restored.total_duration_ms == 35000


# 3. LinUCB A/b matrices round-trip
# 4. Restored LinUCB produces the same arm scores/selections as before saving
def test_linucb_matrices_round_trip_and_selection_equivalence():
    arms = list(MOCK_ARM_PRESETS)
    model = LinUCB(arms=arms, context_dimension=3, alpha=0.5)

    # Train model with diverse updates
    ctx1 = [0.8, 0.8, 1.0]
    ctx2 = [-0.5, 0.5, 1.0]
    model.update(PRESET_ENERGETIC_POSITIVE, ctx1, reward=1.0)
    model.update(PRESET_CALM_POSITIVE, ctx2, reward=0.75)

    # Evaluate selection before serialization
    eval_ctx = [0.7, 0.7, 1.0]
    sel_before = model.select_arm(eval_ctx)

    serialized = serialize_linucb_model(model)
    assert isinstance(serialized, dict)

    restored = deserialize_linucb_model(serialized)

    # Verify identical parameters
    for arm in arms:
        np.testing.assert_array_equal(model.A[arm], restored.A[arm])
        np.testing.assert_array_equal(model.b[arm], restored.b[arm])

    # 4. Restored LinUCB produces identical scores and chosen arm
    sel_after = restored.select_arm(eval_ctx)
    assert sel_after.selected_arm == sel_before.selected_arm
    assert pytest.approx(sel_after.selected_score, rel=1e-6) == sel_before.selected_score
    assert sel_after.arm_scores == sel_before.arm_scores


# 5. Context vectors preserve order and values
# 6. Interaction records preserve recommendation_id/session/preset/context
def test_interaction_records_preservation(in_memory_repo):
    tier3 = {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": "sess_int_01",
        "sequence": 1,
        "audio_time_ms": 1500,
        "emotion": {"valence": 0.65, "arousal": -0.45, "confidence": None},
    }
    ctx = build_context_vector(tier3)
    # Context vector preserves [valence, arousal, bias]
    assert ctx.to_list() == [0.65, -0.45, 1.0]

    interaction = {
        "recommendation_id": "rec_persist_01",
        "session_id": "sess_int_01",
        "recommended_preset_id": PRESET_CALM_POSITIVE,
        "audio_time_ms": 1500,
        "sequence": 1,
        "context_vector": ctx.to_list(),
        "strategy": "cold_start",
        "score": None,
        "feedback_applied": False,
    }

    in_memory_repo.save_interaction(interaction, user_id="user_ctx_test")

    pending = in_memory_repo.load_pending_interactions(user_id="user_ctx_test")
    assert len(pending) == 1
    loaded = pending[0]
    assert loaded["recommendation_id"] == "rec_persist_01"
    assert loaded["session_id"] == "sess_int_01"
    assert loaded["recommended_preset_id"] == PRESET_CALM_POSITIVE
    assert loaded["context_vector"] == [0.65, -0.45, 1.0]
    assert loaded["feedback_applied"] is False

    # Mark applied
    ok = in_memory_repo.mark_interaction_feedback_applied("rec_persist_01")
    assert ok is True
    # Now pending should be empty
    assert len(in_memory_repo.load_pending_interactions(user_id="user_ctx_test")) == 0


# 7. Processed feedback IDs remain unique/idempotent
# 8. Duplicate feedback persistence is rejected safely
def test_feedback_idempotency_and_duplicate_rejection(in_memory_repo):
    fb_record = {
        "feedback_id": "fb_uniq_01",
        "session_id": "sess_fb_01",
        "preset_id": PRESET_ENERGETIC_POSITIVE,
        "feedback_type": "like",
        "reward": 1.0,
        "raw_value": None,
        "is_auxiliary": False,
        "recommendation_id": "rec_01",
    }

    assert in_memory_repo.is_feedback_processed("fb_uniq_01") is False

    # First save succeeds
    saved = in_memory_repo.save_processed_feedback(fb_record, user_id="user_fb_test")
    assert saved is True
    assert in_memory_repo.is_feedback_processed("fb_uniq_01") is True

    # 8. Duplicate persistence rejected safely (returns False)
    saved_again = in_memory_repo.save_processed_feedback(fb_record, user_id="user_fb_test")
    assert saved_again is False

    seen_ids = in_memory_repo.load_processed_feedback_ids("user_fb_test")
    assert "fb_uniq_01" in seen_ids


# 9. Multiple users remain isolated
def test_multiple_users_isolation(in_memory_repo):
    state_a = UserPersonalizationState("user_A")
    state_a.recommendation_count = 10
    state_a.cumulative_reward = 5.0
    state_a.numerical_reward_count = 5

    state_b = UserPersonalizationState("user_B")
    state_b.recommendation_count = 2
    state_b.cumulative_reward = -1.0
    state_b.numerical_reward_count = 1

    in_memory_repo.save_user_state(state_a)
    in_memory_repo.save_user_state(state_b)

    loaded_a = in_memory_repo.load_user_state("user_A")
    loaded_b = in_memory_repo.load_user_state("user_B")

    assert loaded_a is not None and loaded_b is not None
    assert loaded_a.user_id == "user_A"
    assert loaded_b.user_id == "user_B"
    assert loaded_a.recommendation_count == 10
    assert loaded_b.recommendation_count == 2
    assert loaded_a.cumulative_reward == 5.0
    assert loaded_b.cumulative_reward == -1.0


# 10. Multiple preset arms remain isolated
def test_multiple_preset_arms_isolation():
    model = LinUCB(arms=["arm_1", "arm_2"], context_dimension=3, alpha=1.0)
    ctx = [0.8, 0.8, 1.0]

    # Update only arm_1
    model.update("arm_1", ctx, reward=1.0)

    serialized = serialize_linucb_model(model)
    restored = deserialize_linucb_model(serialized)

    # arm_1 has updated A and b
    assert not np.array_equal(restored.A["arm_1"], np.identity(3))
    assert not np.array_equal(restored.b["arm_1"], np.zeros(3))

    # arm_2 is strictly untouched
    np.testing.assert_array_equal(restored.A["arm_2"], np.identity(3))
    np.testing.assert_array_equal(restored.b["arm_2"], np.zeros(3))


# 11. Missing user returns a clean not-found result
def test_missing_user_returns_none(in_memory_repo):
    assert in_memory_repo.load_user_state("non_existent_user") is None
    assert in_memory_repo.load_linucb_state("non_existent_user") is None
    assert restore_adaptive_engine(in_memory_repo, "non_existent_user") is None


# 12. Restored AdaptivePersonalizationEngine has equivalent user state
# 13. Restored successful_learning_updates remain correct
def test_engine_restore_round_trip(in_memory_repo):
    engine = AdaptivePersonalizationEngine(user_id="user_engine_rt", alpha=0.2)

    tier3 = {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": "sess_eng",
        "sequence": 1,
        "audio_time_ms": 1000,
        "emotion": {"valence": 0.8, "arousal": 0.8, "confidence": None},
    }

    # Generate recommendation and process positive feedback
    rec = engine.recommend(tier3, recommendation_sequence=1)
    fb = {
        "schema_version": "1.1",
        "event_type": "feedback.event",
        "session_id": "sess_eng",
        "sequence": 1,
        "audio_time_ms": 1500,
        "feedback_id": "fb_eng_01",
        "preset_id": rec["recommended_preset_id"],
        "feedback": {"type": "like"},
    }
    res = engine.process_feedback(fb)
    assert res.applied is True

    # Persist the engine
    persist_adaptive_engine(in_memory_repo, engine)

    # 12 & 13. Restore engine from persistence
    restored = restore_adaptive_engine(in_memory_repo, user_id="user_engine_rt")
    assert restored is not None

    assert restored.user_state.user_id == "user_engine_rt"
    assert restored.successful_update_count == 1
    assert restored.user_state.successful_learning_updates == 1
    assert restored.is_linucb_active is True
    assert restored.user_state.recommendation_count == 1
    assert restored.user_state.feedback_count == 1
    assert restored.user_state.cumulative_reward == 1.0

    # Ensure future recommendation matches original engine
    rec_orig = engine.recommend(tier3, recommendation_sequence=2)
    rec_restored = restored.recommend(tier3, recommendation_sequence=2)

    assert rec_orig["recommended_preset_id"] == rec_restored["recommended_preset_id"]
    assert rec_orig["strategy"] == rec_restored["strategy"] == "linucb"
    assert pytest.approx(rec_orig["score"], rel=1e-6) == rec_restored["score"]


# 14. JSON serialization contains no NumPy-only values
def test_json_serialization_contains_no_numpy_primitives():
    model = LinUCB(arms=["arm_a"], context_dimension=3)
    model.update("arm_a", [0.5, 0.5, 1.0], reward=1.0)

    serialized = serialize_linucb_model(model)

    # Ensure json.dumps succeeds without TypeError: Object of type float64 is not JSON serializable
    json_str = json.dumps(serialized)
    loaded = json.loads(json_str)

    a_mat = loaded["arms"][0]["a_matrix"]
    b_vec = loaded["arms"][0]["b_vector"]

    for row in a_mat:
        for val in row:
            assert isinstance(val, float)
    for val in b_vec:
        assert isinstance(val, float)


# 15. Invalid matrix/vector dimensions are rejected during restore
def test_invalid_matrix_dimensions_rejected():
    corrupted_data = {
        "arm_id": "arm_bad",
        "a_matrix": [[1.0, 0.0], [0.0, 1.0]],  # 2x2 instead of 3x3
        "b_vector": [0.0, 0.0, 0.0],
    }

    with pytest.raises(ValueError, match="Corrupted or invalid A matrix shape"):
        deserialize_linucb_arm(corrupted_data, expected_dimension=3)

    corrupted_b = {
        "arm_id": "arm_bad",
        "a_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "b_vector": [0.0, 0.0],  # Length 2 instead of 3
    }

    with pytest.raises(ValueError, match="Corrupted or invalid b vector shape"):
        deserialize_linucb_arm(corrupted_b, expected_dimension=3)


def _make_tier3(session_id: str = "sess_001", seq: int = 1, time_ms: int = 1000, valence: float = 0.8, arousal: float = 0.8) -> Dict[str, Any]:
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": session_id,
        "sequence": seq,
        "audio_time_ms": time_ms,
        "emotion": {"valence": valence, "arousal": arousal, "confidence": None},
    }


def test_persistence_restart_preserves_session_sequences_without_duplicate_ids(in_memory_repo):
    """
    Sequence Ownership & Persistence Test:
    1. Three recommendations in session-A -> sequence 0, 1, 2
    2. A new session session-B -> starts at sequence 0
    3. Recommendation IDs follow rec_<session_id>_<sequence> and are unique across sessions
    4. Persistence and restart restores session sequences so continued sessions do NOT duplicate IDs
    5. User analytics counter recommendation_count is tracked separately as a lifetime counter
    """
    engine = AdaptivePersonalizationEngine(user_id="user_restart_seq_persist")

    # 1. Three recommendations in session-A
    recs_a = []
    for i in range(3):
        t3 = _make_tier3(session_id="session-A", seq=i + 1, time_ms=(i + 1) * 1000)
        recs_a.append(engine.recommend(t3))

    assert [r["sequence"] for r in recs_a] == [0, 1, 2]
    assert [r["recommendation_id"] for r in recs_a] == [
        generate_recommendation_id("session-A", 0, "user_restart_seq_persist"),
        generate_recommendation_id("session-A", 1, "user_restart_seq_persist"),
        generate_recommendation_id("session-A", 2, "user_restart_seq_persist"),
    ]

    # 2. A new session session-B starts at sequence 0
    recs_b = []
    for i in range(2):
        t3 = _make_tier3(session_id="session-B", seq=i + 1, time_ms=(i + 1) * 1000)
        recs_b.append(engine.recommend(t3))

    assert [r["sequence"] for r in recs_b] == [0, 1]
    assert [r["recommendation_id"] for r in recs_b] == [
        generate_recommendation_id("session-B", 0, "user_restart_seq_persist"),
        generate_recommendation_id("session-B", 1, "user_restart_seq_persist"),
    ]

    # 3. Recommendation IDs are unique across all sessions
    all_ids = [r["recommendation_id"] for r in recs_a + recs_b]
    assert len(set(all_ids)) == 5
    for r_id in all_ids:
        assert r_id.startswith("rec_")
        assert len(r_id) == 36
    assert engine.user_state.recommendation_count == 5

    # 4. Persist and restore engine
    persist_adaptive_engine(in_memory_repo, engine)
    restored = restore_adaptive_engine(in_memory_repo, user_id="user_restart_seq_persist")
    assert restored is not None

    # session-A continues from sequence 3 -> generate_recommendation_id (no duplicate IDs)
    t3_a_cont = _make_tier3(session_id="session-A", seq=4, time_ms=4000)
    rec_a3 = restored.recommend(t3_a_cont)
    assert rec_a3["sequence"] == 3
    assert rec_a3["recommendation_id"] == generate_recommendation_id("session-A", 3, "user_restart_seq_persist")

    # session-B continues from sequence 2 -> generate_recommendation_id
    t3_b_cont = _make_tier3(session_id="session-B", seq=3, time_ms=3000)
    rec_b2 = restored.recommend(t3_b_cont)
    assert rec_b2["sequence"] == 2
    assert rec_b2["recommendation_id"] == generate_recommendation_id("session-B", 2, "user_restart_seq_persist")

    # brand new session session-C starts at sequence 0 -> generate_recommendation_id
    t3_c = _make_tier3(session_id="session-C", seq=1, time_ms=1000)
    rec_c0 = restored.recommend(t3_c)
    assert rec_c0["sequence"] == 0
    assert rec_c0["recommendation_id"] == generate_recommendation_id("session-C", 0, "user_restart_seq_persist")

    # Lifetime recommendation counter in user_state is 8
    assert restored.user_state.recommendation_count == 8


def test_persistence_cross_user_same_session_no_collision(in_memory_repo):
    """
    Direct persistence test:
    User A and User B sharing the same session_id:
    - start sequence at 0
    - produce distinct recommendation IDs (rec_<uuid5_hex>)
    - interactions persist without unique constraint violations
    - both can be restored and resume correct per-user sequences
    """
    user_a = "user_pers_A"
    user_b = "user_pers_B"
    shared_session = "sess_collision_check"

    engine_a = AdaptivePersonalizationEngine(user_id=user_a)
    engine_b = AdaptivePersonalizationEngine(user_id=user_b)

    # Both users generate recommendations for the shared session
    t3 = _make_tier3(session_id=shared_session, seq=1, time_ms=1000)
    rec_a0 = engine_a.recommend(t3)
    rec_b0 = engine_b.recommend(t3)

    assert rec_a0["sequence"] == 0
    assert rec_b0["sequence"] == 0
    assert rec_a0["recommendation_id"] == generate_recommendation_id(shared_session, 0, user_a)
    assert rec_b0["recommendation_id"] == generate_recommendation_id(shared_session, 0, user_b)
    assert rec_a0["recommendation_id"] != rec_b0["recommendation_id"]
    assert len(rec_a0["recommendation_id"]) == 36
    assert len(rec_b0["recommendation_id"]) == 36

    # Persist both engines to the same repository
    persist_adaptive_engine(in_memory_repo, engine_a)
    persist_adaptive_engine(in_memory_repo, engine_b)

    # Verify both interactions persisted cleanly without collision
    pending_a = in_memory_repo.load_pending_interactions(user_id=user_a)
    pending_b = in_memory_repo.load_pending_interactions(user_id=user_b)
    assert len(pending_a) == 1
    assert len(pending_b) == 1
    assert pending_a[0]["recommendation_id"] == rec_a0["recommendation_id"]
    assert pending_b[0]["recommendation_id"] == rec_b0["recommendation_id"]

    # Restore both engines
    restored_a = restore_adaptive_engine(in_memory_repo, user_id=user_a)
    restored_b = restore_adaptive_engine(in_memory_repo, user_id=user_b)
    assert restored_a is not None
    assert restored_b is not None

    # Both resume sequence at 1 without duplicate IDs
    rec_a1 = restored_a.recommend(_make_tier3(session_id=shared_session, seq=2, time_ms=2000))
    rec_b1 = restored_b.recommend(_make_tier3(session_id=shared_session, seq=2, time_ms=2000))

    assert rec_a1["sequence"] == 1
    assert rec_b1["sequence"] == 1
    assert rec_a1["recommendation_id"] == generate_recommendation_id(shared_session, 1, user_a)
    assert rec_b1["recommendation_id"] == generate_recommendation_id(shared_session, 1, user_b)
    assert rec_a1["recommendation_id"] != rec_b1["recommendation_id"]


def test_recommendation_id_hardening_long_identifiers_and_fixed_length(in_memory_repo):
    """
    Hardening Test:
    1. very long user_id
    2. very long session_id
    3. two users with the same session_id
    4. restart continuation
    5. recommendation_id length remains within DB column limit (VARCHAR(128))
    6. no persistence collision
    """
    # 1 & 2. Very long user_id and session_id (e.g. 120 chars each, close to VARCHAR(128) max)
    long_user_a = "user_alpha_" + ("x" * 105)
    long_user_b = "user_beta_" + ("y" * 106)
    long_session = "sess_long_" + ("z" * 105)

    assert len(long_user_a) == 116
    assert len(long_user_b) == 116
    assert len(long_session) == 115

    # 5. recommendation_id length remains strictly bounded (exactly 36 chars) <= 128
    rec_id_a0 = generate_recommendation_id(long_session, 0, long_user_a)
    rec_id_b0 = generate_recommendation_id(long_session, 0, long_user_b)

    assert len(rec_id_a0) == 36
    assert len(rec_id_b0) == 36
    assert len(rec_id_a0) <= 128

    # Even with 5,000 char strings, output length is strictly 36
    assert len(generate_recommendation_id("s" * 5000, 0, "u" * 5000)) == 36

    # 3. Two users with the same session_id have distinct IDs
    assert rec_id_a0 != rec_id_b0

    # 6. No persistence collision: persist both to database
    engine_a = AdaptivePersonalizationEngine(user_id=long_user_a)
    engine_b = AdaptivePersonalizationEngine(user_id=long_user_b)

    t3 = _make_tier3(session_id=long_session, seq=1, time_ms=1000)
    rec_a = engine_a.recommend(t3)
    rec_b = engine_b.recommend(t3)

    assert rec_a["recommendation_id"] == rec_id_a0
    assert rec_b["recommendation_id"] == rec_id_b0

    persist_adaptive_engine(in_memory_repo, engine_a)
    persist_adaptive_engine(in_memory_repo, engine_b)

    # 4. Restart continuation does not collide and resumes per-session sequence
    restored_a = restore_adaptive_engine(in_memory_repo, long_user_a)
    restored_b = restore_adaptive_engine(in_memory_repo, long_user_b)

    rec_a_next = restored_a.recommend(_make_tier3(session_id=long_session, seq=2, time_ms=2000))
    rec_b_next = restored_b.recommend(_make_tier3(session_id=long_session, seq=2, time_ms=2000))

    assert rec_a_next["sequence"] == 1
    assert rec_b_next["sequence"] == 1
    assert len(rec_a_next["recommendation_id"]) == 36
    assert len(rec_b_next["recommendation_id"]) == 36
    assert rec_a_next["recommendation_id"] != rec_b_next["recommendation_id"]
    assert rec_a_next["recommendation_id"] != rec_id_a0


# Live PostgreSQL Integration (Conditional)
def test_live_postgresql_integration():
    """
    Attempts connection to actual PostgreSQL server at DATABASE_URL.
    If PostgreSQL is unreachable, skips cleanly without failing CI.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL environment variable not set - skipping live PostgreSQL test")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            pass
    except Exception as exc:
        pytest.skip(f"Live PostgreSQL server not reachable at {db_url}: {exc}")

    # If reachable, execute table creation and repository round-trip on PostgreSQL
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    repo = PersonalizationRepository(session_factory=session_factory)

    state = UserPersonalizationState("pg_live_user")
    state.recommendation_count = 1
    repo.save_user_state(state)

    loaded = repo.load_user_state("pg_live_user")
    assert loaded is not None
    assert loaded.user_id == "pg_live_user"
