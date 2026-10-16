"""
Automated Test Suite for Milestone 8: FastAPI Runtime Integration.

Covers all 17 verification points from STEP 10:
1. New user recommendation works.
2. First recommendation uses cold_start.
3. Recommendation validates against Contract v1.1.
4. Recommendation preserves session_id and audio_time_ms.
5. Like feedback applies +1 reward.
6. Dislike feedback applies -1 reward.
7. Feedback triggers LinUCB learning.
8. Next recommendation switches to strategy=linucb after successful learning.
9. Duplicate feedback does not update twice.
10. Unmatched feedback is handled cleanly.
11. view_duration does not update LinUCB.
12. User state endpoint reflects recommendation/feedback counts.
13. User A and User B remain isolated (Viva Demo Scenario).
14. Runtime reconstruction restores persisted user state.
15. Runtime reconstruction restores LinUCB state.
16. Feedback idempotency survives runtime reconstruction.
17. Existing /health and mock MER routes continue working.
"""

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))
_main_mod = importlib.import_module("app.main")
_routes_mod = importlib.import_module("app.personalization_routes")

app = _main_mod.app
get_personalization_service = _routes_mod.get_personalization_service
set_personalization_service = _routes_mod.set_personalization_service
from components.personalization import (
    Base,
    MAX_IDENTIFIER_LENGTH,
    PersonalizationRepository,
    PersonalizationRuntimeService,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    generate_recommendation_id,
)

REC_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "recommendation.schema.json"
TIER3_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "mer-tier3.schema.json"
FEEDBACK_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "feedback-event.schema.json"

with open(REC_SCHEMA_PATH, "r", encoding="utf-8") as f:
    REC_VALIDATOR = Draft202012Validator(json.load(f))


def make_tier3(session_id="sess_001", seq=1, time_ms=1000, valence=0.8, arousal=0.8):
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": session_id,
        "sequence": seq,
        "audio_time_ms": time_ms,
        "emotion": {
            "valence": valence,
            "arousal": arousal,
            "confidence": None,
        },
    }


def make_feedback(
    session_id="sess_001",
    seq=1,
    time_ms=1500,
    fb_id="fb_001",
    preset_id=PRESET_ENERGETIC_POSITIVE,
    fb_type="like",
    rating=None,
    duration_ms=None,
):
    fb_dict = {"type": fb_type}
    if rating is not None:
        fb_dict["rating"] = rating
    if duration_ms is not None:
        fb_dict["duration_ms"] = duration_ms

    return {
        "schema_version": "1.1",
        "event_type": "feedback.event",
        "session_id": session_id,
        "sequence": seq,
        "audio_time_ms": time_ms,
        "feedback_id": fb_id,
        "preset_id": preset_id,
        "feedback": fb_dict,
    }


@pytest.fixture
def in_memory_repo() -> PersonalizationRepository:
    """Isolated SQLite database repository fixture with persistent in-memory StaticPool."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return PersonalizationRepository(session_factory=session_factory)


@pytest.fixture
def runtime_service(in_memory_repo) -> PersonalizationRuntimeService:
    """PersonalizationRuntimeService backed by the isolated test repository."""
    svc = PersonalizationRuntimeService(repository=in_memory_repo)
    set_personalization_service(svc)
    return svc


@pytest.fixture
def client(runtime_service) -> TestClient:
    """TestClient wired with the isolated test service."""
    return TestClient(app)


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_new_user_recommendation_and_cold_start(client):
    """
    Points 1, 2, 3, 4:
    - New user recommendation works.
    - First recommendation uses cold_start.
    - Validates against Contract v1.1 recommendation.schema.json.
    - Preserves session_id and audio_time_ms.
    """
    t3 = make_tier3(session_id="session-user-1", seq=1, time_ms=2500, valence=0.7, arousal=0.7)
    res = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-test-01", "tier3_event": t3},
    )
    assert res.status_code == 200
    data = res.json()

    # Contract v1.1 Validation
    errors = list(REC_VALIDATOR.iter_errors(data))
    assert not errors, f"Schema validation errors: {errors}"

    # Verify strategy and score
    assert data["strategy"] == "cold_start"
    assert data["score"] is None
    assert data["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE

    # Verify metadata preservation
    assert data["session_id"] == "session-user-1"
    assert data["audio_time_ms"] == 2500
    assert "recommendation_id" in data


def test_like_feedback_applies_positive_reward(client):
    """Point 5: Like feedback applies +1 reward."""
    t3 = make_tier3(session_id="sess_like", seq=1, time_ms=1000, valence=0.8, arousal=0.8)
    rec_res = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-like", "tier3_event": t3},
    )
    assert rec_res.status_code == 200
    preset_id = rec_res.json()["recommended_preset_id"]

    fb = make_feedback(
        session_id="sess_like",
        fb_id="fb_like_01",
        preset_id=preset_id,
        fb_type="like",
    )
    fb_res = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-like", "feedback_event": fb},
    )
    assert fb_res.status_code == 200
    fb_data = fb_res.json()

    assert fb_data["status"] == "applied"
    assert fb_data["applied"] is True
    assert fb_data["reward"] == 1.0
    assert fb_data["arm_updated"] == preset_id


def test_dislike_feedback_applies_negative_reward(client):
    """Point 6: Dislike feedback applies -1 reward."""
    t3 = make_tier3(session_id="sess_dislike", seq=1, time_ms=1000, valence=0.8, arousal=0.8)
    rec_res = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-dislike", "tier3_event": t3},
    )
    preset_id = rec_res.json()["recommended_preset_id"]

    fb = make_feedback(
        session_id="sess_dislike",
        fb_id="fb_dislike_01",
        preset_id=preset_id,
        fb_type="dislike",
    )
    fb_res = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-dislike", "feedback_event": fb},
    )
    assert fb_res.status_code == 200
    fb_data = fb_res.json()

    assert fb_data["status"] == "applied"
    assert fb_data["applied"] is True
    assert fb_data["reward"] == -1.0


def test_feedback_triggers_linucb_strategy_switch(client):
    """Points 7 & 8: Feedback triggers LinUCB learning and next recommendation switches to strategy=linucb."""
    t3 = make_tier3(session_id="sess_switch", seq=1, time_ms=1000, valence=0.5, arousal=0.5)

    # 1. First recommendation is cold_start
    rec1 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-switch", "tier3_event": t3},
    ).json()
    assert rec1["strategy"] == "cold_start"
    assert rec1["score"] is None

    # 2. Process feedback
    fb = make_feedback(
        session_id="sess_switch",
        fb_id="fb_switch_01",
        preset_id=rec1["recommended_preset_id"],
        fb_type="like",
    )
    fb_res = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-switch", "feedback_event": fb},
    ).json()
    assert fb_res["applied"] is True

    # 3. Second recommendation has switched to linucb
    t3_2 = make_tier3(session_id="sess_switch", seq=2, time_ms=2000, valence=0.5, arousal=0.5)
    rec2 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-switch", "tier3_event": t3_2},
    ).json()

    assert rec2["strategy"] == "linucb"
    assert isinstance(rec2["score"], float)
    assert rec2["score"] > 0.0


def test_duplicate_feedback_protection(client):
    """Point 9: Duplicate feedback does not update model twice."""
    t3 = make_tier3(session_id="sess_dup", seq=1, time_ms=1000, valence=0.8, arousal=0.8)
    rec = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-dup", "tier3_event": t3},
    ).json()

    fb = make_feedback(
        session_id="sess_dup",
        fb_id="fb_dup_unique_01",
        preset_id=rec["recommended_preset_id"],
        fb_type="like",
    )

    # First submission
    res1 = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-dup", "feedback_event": fb},
    ).json()
    assert res1["status"] == "applied"
    assert res1["applied"] is True

    # Duplicate submission with identical feedback_id
    res2 = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-dup", "feedback_event": fb},
    ).json()
    assert res2["status"] == "duplicate"
    assert res2["applied"] is False

    # Verify state has exactly 1 learning update
    state = client.get("/api/personalization/users/user-dup/state").json()
    assert state["successful_learning_updates"] == 1
    assert state["feedback_count"] == 1


def test_unmatched_feedback_handling(client):
    """Point 10: Unmatched feedback is handled cleanly without exceptions."""
    fb = make_feedback(
        session_id="sess_nonexistent",
        fb_id="fb_unmatched_01",
        preset_id="mock-calm-negative",
        fb_type="like",
    )
    res = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-unmatched", "feedback_event": fb},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "unmatched"
    assert data["applied"] is False
    assert "No pending unprocessed recommendation found" in data["message"]


def test_view_duration_does_not_update_linucb(client):
    """Point 11: Auxiliary view_duration feedback does not update LinUCB."""
    t3 = make_tier3(session_id="sess_view", seq=1, time_ms=1000, valence=0.8, arousal=0.8)
    rec = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-view", "tier3_event": t3},
    ).json()

    fb = make_feedback(
        session_id="sess_view",
        fb_id="fb_view_01",
        preset_id=rec["recommended_preset_id"],
        fb_type="view_duration",
        duration_ms=45000,
    )
    res = client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-view", "feedback_event": fb},
    ).json()

    assert res["status"] == "auxiliary"
    assert res["applied"] is False
    assert res["reward"] is None

    # LinUCB should NOT be active since successful_learning_updates is 0
    t3_next = make_tier3(session_id="sess_view", seq=2, time_ms=2000, valence=0.8, arousal=0.8)
    rec2 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-view", "tier3_event": t3_next},
    ).json()
    assert rec2["strategy"] == "cold_start"

    # User state should record the duration
    state = client.get("/api/personalization/users/user-view/state").json()
    assert state["successful_learning_updates"] == 0
    stats = state["preset_stats"][rec["recommended_preset_id"]]
    assert stats["view_duration_count"] == 1
    assert stats["total_duration_ms"] == 45000


def test_user_state_endpoint(client):
    """Point 12: User state endpoint reflects recommendation/feedback counts and returns 404 for missing users."""
    # 404 for nonexistent user
    missing = client.get("/api/personalization/users/nonexistent-user-999/state")
    assert missing.status_code == 404

    # Perform recommendation and feedback
    t3 = make_tier3(session_id="sess_state", seq=1, time_ms=1000, valence=0.6, arousal=0.6)
    client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-state-check", "tier3_event": t3},
    )
    fb = make_feedback(
        session_id="sess_state",
        fb_id="fb_state_01",
        preset_id=PRESET_ENERGETIC_POSITIVE,
        fb_type="rating",
        rating=5,
    )
    client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-state-check", "feedback_event": fb},
    )

    state = client.get("/api/personalization/users/user-state-check/state").json()
    assert state["user_id"] == "user-state-check"
    assert state["recommendation_count"] == 1
    assert state["feedback_count"] == 1
    assert state["successful_learning_updates"] == 1
    assert state["last_recommended_preset"] == PRESET_ENERGETIC_POSITIVE
    assert state["last_feedback_type"] == "rating"
    assert state["average_reward"] == 1.0
    assert "preference_summary" in state
    assert "preset_stats" in state


def test_multi_user_isolation_and_viva_demo(client):
    """
    Points 13 & STEP 11 (Viva Demo Scenario):
    User A and User B with identical valence/arousal develop different personalization
    states and receive different preset recommendations based on divergent feedback.
    """
    context_emotion = make_tier3(session_id="sess_viva", seq=1, time_ms=1000, valence=0.8, arousal=0.8)

    # 1. Both receive cold-start energetic-positive initially
    rec_a1 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-A", "tier3_event": context_emotion},
    ).json()
    rec_b1 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-B", "tier3_event": context_emotion},
    ).json()

    assert rec_a1["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE
    assert rec_b1["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE

    # 2. User A likes energetic-positive (+1.0 reward)
    client.post(
        "/api/personalization/feedback",
        json={
            "user_id": "user-A",
            "feedback_event": make_feedback(
                session_id="sess_viva",
                fb_id="fb_viva_A1",
                preset_id=PRESET_ENERGETIC_POSITIVE,
                fb_type="like",
            ),
        },
    )

    # 3. User B dislikes energetic-positive (-1.0 reward)
    client.post(
        "/api/personalization/feedback",
        json={
            "user_id": "user-B",
            "feedback_event": make_feedback(
                session_id="sess_viva",
                fb_id="fb_viva_B1",
                preset_id=PRESET_ENERGETIC_POSITIVE,
                fb_type="dislike",
            ),
        },
    )

    # 4. Same emotional context presented again
    context_emotion2 = make_tier3(session_id="sess_viva", seq=2, time_ms=2000, valence=0.8, arousal=0.8)
    rec_a2 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-A", "tier3_event": context_emotion2},
    ).json()
    rec_b2 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-B", "tier3_event": context_emotion2},
    ).json()

    # Both switched to LinUCB
    assert rec_a2["strategy"] == "linucb"
    assert rec_b2["strategy"] == "linucb"

    # User A continues to receive energetic-positive (high UCB score)
    assert rec_a2["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE

    # User B receives a DIFFERENT preset arm because energetic-positive was penalized
    assert rec_b2["recommended_preset_id"] != PRESET_ENERGETIC_POSITIVE


def test_runtime_reconstruction_and_restart(in_memory_repo, client):
    """
    Points 14, 15, 16:
    - Runtime reconstruction restores persisted user state.
    - Runtime reconstruction restores LinUCB state.
    - Feedback idempotency survives runtime reconstruction.
    """
    t3 = make_tier3(session_id="sess_rst", seq=1, time_ms=1000, valence=0.7, arousal=0.7)
    rec = client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-restart-test", "tier3_event": t3},
    ).json()

    fb = make_feedback(
        session_id="sess_rst",
        fb_id="fb_restart_01",
        preset_id=rec["recommended_preset_id"],
        fb_type="like",
    )
    client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-restart-test", "feedback_event": fb},
    )

    # Simulate process restart by instantiating a completely new PersonalizationRuntimeService
    new_svc = PersonalizationRuntimeService(repository=in_memory_repo)
    set_personalization_service(new_svc)
    restarted_client = TestClient(app)

    # 14 & 15. Verify restored state and LinUCB activation
    state = restarted_client.get("/api/personalization/users/user-restart-test/state").json()
    assert state["recommendation_count"] == 1
    assert state["feedback_count"] == 1
    assert state["successful_learning_updates"] == 1
    assert state["average_reward"] == 1.0

    # 16. Verify feedback idempotency survives restart (duplicate rejected)
    dup_fb = make_feedback(
        session_id="sess_rst",
        fb_id="fb_restart_01",
        preset_id=rec["recommended_preset_id"],
        fb_type="like",
    )
    dup_res = restarted_client.post(
        "/api/personalization/feedback",
        json={"user_id": "user-restart-test", "feedback_event": dup_fb},
    ).json()
    assert dup_res["status"] == "duplicate"
    assert dup_res["applied"] is False

    # Future recommendation continues on LinUCB
    t3_next = make_tier3(session_id="sess_rst", seq=2, time_ms=2000, valence=0.7, arousal=0.7)
    next_rec = restarted_client.post(
        "/api/personalization/recommend",
        json={"user_id": "user-restart-test", "tier3_event": t3_next},
    ).json()
    assert next_rec["strategy"] == "linucb"


def test_existing_health_and_mock_mer_routes(client):
    """Point 17: Existing /health and WebSocket routes continue working unmodified."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json() == {"status": "ok"}

    # Verify routes registered
    route_paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/health" in route_paths
    assert "/ws/mock/mer-tier3" in route_paths
    assert "/ws/mock/mer" in route_paths


def test_request_validation_errors(client):
    """Verify clean 422 HTTP errors on invalid input schemas or missing user_id."""
    # 1. Empty user_id
    res = client.post(
        "/api/personalization/recommend",
        json={"user_id": "  ", "tier3_event": make_tier3()},
    )
    assert res.status_code == 422

    # 2. Invalid tier3_event (missing required field 'emotion')
    bad_t3 = {"schema_version": "1.1", "event_type": "mer.tier3", "session_id": "s1", "sequence": 1, "audio_time_ms": 100}
    res2 = client.post(
        "/api/personalization/recommend",
        json={"user_id": "u1", "tier3_event": bad_t3},
    )
    assert res2.status_code == 422

    # 3. Invalid feedback_event (invalid feedback type)
    bad_fb = {
        "schema_version": "1.1",
        "event_type": "feedback.event",
        "session_id": "s1",
        "sequence": 1,
        "audio_time_ms": 100,
        "feedback_id": "fb1",
        "preset_id": "p1",
        "feedback": {"type": "not_a_valid_type"},
    }
    res3 = client.post(
        "/api/personalization/feedback",
        json={"user_id": "u1", "feedback_event": bad_fb},
    )
    assert res3.status_code == 422


def test_recommendation_sequence_and_id_uniqueness(client, in_memory_repo):
    """
    Review Item:
    Confirm recommendation sequence is scoped per session_id (not lifelong user counter):
    1. Three recommendations in session-A -> sequence 0, 1, 2
    2. A new session session-B -> sequence starts at 0
    3. Recommendation IDs remain unique across both sessions
    4. Persistence/restart continues an existing session without duplicate recommendation IDs
    5. User state recommendation_count tracks lifetime analytics separately (total = 6)
    """
    user_id = "user-multi-session-test"

    # 1. Three recommendations in session-A
    sess_a_recs = []
    sess_a_seqs = []
    for i in range(3):
        t3 = make_tier3(session_id="session-A", seq=i + 1, time_ms=(i + 1) * 1000)
        res = client.post(
            "/api/personalization/recommend",
            json={"user_id": user_id, "tier3_event": t3},
        )
        assert res.status_code == 200
        data = res.json()
        sess_a_recs.append(data["recommendation_id"])
        sess_a_seqs.append(data["sequence"])

    assert sess_a_seqs == [0, 1, 2]
    assert sess_a_recs == [
        generate_recommendation_id("session-A", 0, user_id),
        generate_recommendation_id("session-A", 1, user_id),
        generate_recommendation_id("session-A", 2, user_id),
    ]

    # 2. A new session session-B starts at sequence 0
    sess_b_recs = []
    sess_b_seqs = []
    for i in range(2):
        t3 = make_tier3(session_id="session-B", seq=i + 1, time_ms=(i + 1) * 1000)
        res = client.post(
            "/api/personalization/recommend",
            json={"user_id": user_id, "tier3_event": t3},
        )
        assert res.status_code == 200
        data = res.json()
        sess_b_recs.append(data["recommendation_id"])
        sess_b_seqs.append(data["sequence"])

    assert sess_b_seqs == [0, 1]
    assert sess_b_recs == [
        generate_recommendation_id("session-B", 0, user_id),
        generate_recommendation_id("session-B", 1, user_id),
    ]

    # 3. Recommendation IDs are unique across all sessions
    all_recs = sess_a_recs + sess_b_recs
    assert len(set(all_recs)) == 5
    for r_id in all_recs:
        assert r_id.startswith("rec_")
        assert len(r_id) == 36

    # Check user analytics counter reflects lifetime total (3 in session-A + 2 in session-B = 5)
    state = client.get(f"/api/personalization/users/{user_id}/state").json()
    assert state["recommendation_count"] == 5

    # 4. Simulate restart: instantiate brand new runtime service bound to same repo
    new_svc = PersonalizationRuntimeService(repository=in_memory_repo)
    set_personalization_service(new_svc)
    restarted_client = TestClient(app)

    # Next recommendation in session-A continues at sequence 3 (no duplicate IDs)
    t3_a_next = make_tier3(session_id="session-A", seq=4, time_ms=4000)
    res_restart = restarted_client.post(
        "/api/personalization/recommend",
        json={"user_id": user_id, "tier3_event": t3_a_next},
    )
    assert res_restart.status_code == 200
    data_restart = res_restart.json()
    assert data_restart["sequence"] == 3
    assert data_restart["recommendation_id"] == generate_recommendation_id("session-A", 3, user_id)

    # Lifetime analytics counter updated to 6
    state_after = restarted_client.get(f"/api/personalization/users/{user_id}/state").json()
    assert state_after["recommendation_count"] == 6


def test_recommendation_id_cross_user_isolation_same_session(client, in_memory_repo):
    """
    Review Item:
    Confirm recommendation_id uniqueness across different users sharing the same session_id:
    1. User A and User B can use the same session_id (e.g. "shared-session-100")
    2. Both start sequence at 0
    3. Recommendation IDs are distinct (rec_<user_id>_<session_id>_<sequence>)
    4. Persistence does not collide in database
    5. Restart preserves correct independent sequences for each user/session
    """
    user_a = "user-shared-sess-A"
    user_b = "user-shared-sess-B"
    shared_session = "shared-session-100"

    # 1. User A generates two recommendations in shared_session
    recs_a = []
    for i in range(2):
        t3 = make_tier3(session_id=shared_session, seq=i + 1, time_ms=(i + 1) * 1000)
        res = client.post("/api/personalization/recommend", json={"user_id": user_a, "tier3_event": t3})
        assert res.status_code == 200
        recs_a.append(res.json())

    # 2. User B generates two recommendations in the exact same shared_session
    recs_b = []
    for i in range(2):
        t3 = make_tier3(session_id=shared_session, seq=i + 1, time_ms=(i + 1) * 1000)
        res = client.post("/api/personalization/recommend", json={"user_id": user_b, "tier3_event": t3})
        assert res.status_code == 200
        recs_b.append(res.json())

    # Both users started sequence at 0 and advanced independently: [0, 1]
    assert [r["sequence"] for r in recs_a] == [0, 1]
    assert [r["sequence"] for r in recs_b] == [0, 1]

    # Recommendation IDs include user scope and are strictly distinct
    assert [r["recommendation_id"] for r in recs_a] == [
        generate_recommendation_id(shared_session, 0, user_a),
        generate_recommendation_id(shared_session, 1, user_a),
    ]
    assert [r["recommendation_id"] for r in recs_b] == [
        generate_recommendation_id(shared_session, 0, user_b),
        generate_recommendation_id(shared_session, 1, user_b),
    ]

    all_ids = [r["recommendation_id"] for r in recs_a + recs_b]
    assert len(set(all_ids)) == 4
    for r_id in all_ids:
        assert r_id.startswith("rec_")
        assert len(r_id) == 36

    # 3. Persistence does not collide: both users have their own interactions in the repository
    pending_a = in_memory_repo.load_pending_interactions(user_id=user_a)
    pending_b = in_memory_repo.load_pending_interactions(user_id=user_b)
    assert len(pending_a) == 2
    assert len(pending_b) == 2

    # 4. Restart preserves correct sequences for each user/session
    restarted_svc = PersonalizationRuntimeService(repository=in_memory_repo)
    set_personalization_service(restarted_svc)
    restarted_client = TestClient(app)

    # User A continues at sequence 2
    t3_a_next = make_tier3(session_id=shared_session, seq=3, time_ms=3000)
    rec_a2 = restarted_client.post(
        "/api/personalization/recommend",
        json={"user_id": user_a, "tier3_event": t3_a_next},
    ).json()
    assert rec_a2["sequence"] == 2
    assert rec_a2["recommendation_id"] == generate_recommendation_id(shared_session, 2, user_a)

    # User B continues at sequence 2
    t3_b_next = make_tier3(session_id=shared_session, seq=3, time_ms=3000)
    rec_b2 = restarted_client.post(
        "/api/personalization/recommend",
        json={"user_id": user_b, "tier3_event": t3_b_next},
    ).json()
    assert rec_b2["sequence"] == 2
    assert rec_b2["recommendation_id"] == generate_recommendation_id(shared_session, 2, user_b)

    assert rec_a2["recommendation_id"] != rec_b2["recommendation_id"]
    assert restarted_client.get(f"/api/personalization/users/{user_a}/state").json()["recommendation_count"] == 3
    assert restarted_client.get(f"/api/personalization/users/{user_b}/state").json()["recommendation_count"] == 3


def test_database_fallback_and_error_surfacing():
    """
    Review Item 2:
    - DATABASE_URL absent: explicit in-memory mode works cleanly.
    - Configured but failing database: does NOT silently pretend persistence succeeded,
      surfaces a controlled RuntimeError.
    """
    # 1. Explicit in-memory mode (repository is None)
    in_memory_svc = PersonalizationRuntimeService(repository=None)
    assert in_memory_svc.repository is None

    t3 = make_tier3(session_id="sess_pure_mem", seq=1, time_ms=1000)
    rec = in_memory_svc.recommend(user_id="user_mem", tier3_event=t3)
    assert rec["strategy"] == "cold_start"

    fb = make_feedback(session_id="sess_pure_mem", fb_id="fb_mem_1", preset_id=rec["recommended_preset_id"], fb_type="like")
    fb_res = in_memory_svc.process_feedback(user_id="user_mem", feedback_event=fb)
    assert fb_res["applied"] is True

    # 2. Configured database failure surfaces a clear controlled error
    # (simulate unreachable database with invalid connection parameters)
    failing_engine = create_engine("sqlite:///nonexistent_path/cannot_create_dir/db.sqlite")
    failing_repo = PersonalizationRepository(session_factory=sessionmaker(bind=failing_engine))
    failing_svc = PersonalizationRuntimeService(repository=failing_repo)

    with pytest.raises(RuntimeError, match="Database persistence"):
        failing_svc.recommend(user_id="user_failing_db", tier3_event=t3)


def test_runtime_service_constructor_repository_semantics(monkeypatch):
    """
    Verify constructor repository semantics across all required cases:
    1. Omitted repository + no DATABASE_URL -> in-memory (repository is None)
    2. Omitted repository + DATABASE_URL -> persistent repository (auto-configured)
    3. Explicit repository=None + DATABASE_URL -> still in-memory (repository is None)
    4. FastAPI dependency provider get_personalization_service() uses automatic configuration
    """
    dummy_db_url = "sqlite:///:memory:"

    # Case 1: omitted repository + no DATABASE_URL -> in-memory
    monkeypatch.delenv("DATABASE_URL", raising=False)
    svc_no_env = PersonalizationRuntimeService()
    assert svc_no_env.repository is None

    # Case 2: omitted repository + DATABASE_URL -> persistent repository
    monkeypatch.setenv("DATABASE_URL", dummy_db_url)
    svc_with_env = PersonalizationRuntimeService()
    assert svc_with_env.repository is not None
    assert isinstance(svc_with_env.repository, PersonalizationRepository)

    # Case 3: explicit repository=None + DATABASE_URL -> still in-memory
    monkeypatch.setenv("DATABASE_URL", dummy_db_url)
    svc_forced_mem = PersonalizationRuntimeService(repository=None)
    assert svc_forced_mem.repository is None

    # Case 4: FastAPI startup / dependency provider automatic DATABASE_URL configuration
    try:
        # With DATABASE_URL set
        set_personalization_service(None)
        monkeypatch.setenv("DATABASE_URL", dummy_db_url)
        fastapi_svc = get_personalization_service()
        assert fastapi_svc.repository is not None
        assert isinstance(fastapi_svc.repository, PersonalizationRepository)

        # With DATABASE_URL absent
        set_personalization_service(None)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        fastapi_svc_mem = get_personalization_service()
        assert fastapi_svc_mem.repository is None
    finally:
        set_personalization_service(None)


def test_concurrency_safety_same_user(runtime_service):
    """
    Review Item 3:
    Simultaneous operations for the same cached user are serialized via per-user locks
    and do not corrupt internal engine state.
    """
    import concurrent.futures

    user_id = "user-concurrent-test"
    t3 = make_tier3(session_id="sess_concurrent", seq=1, time_ms=1000)

    # First get an initial recommendation
    initial_rec = runtime_service.recommend(user_id=user_id, tier3_event=t3)
    target_preset = initial_rec["recommended_preset_id"]

    def do_recommend(idx):
        evt = make_tier3(session_id="sess_concurrent", seq=idx + 2, time_ms=(idx + 2) * 1000)
        return runtime_service.recommend(user_id=user_id, tier3_event=evt)

    def do_feedback(idx):
        fb = make_feedback(
            session_id="sess_concurrent",
            fb_id=f"fb_conc_{idx}",
            preset_id=target_preset,
            fb_type="view_duration",
            duration_ms=1000,
        )
        return runtime_service.process_feedback(user_id=user_id, feedback_event=fb)

    # Run 10 recommendation and 5 feedback operations concurrently across worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        rec_futures = [executor.submit(do_recommend, i) for i in range(10)]
        fb_futures = [executor.submit(do_feedback, i) for i in range(5)]
        recs = [f.result() for f in rec_futures]
        fbs = [f.result() for f in fb_futures]

    assert len(recs) == 10
    assert len(fbs) == 5

    # Check that recommendation IDs are all unique
    all_rec_ids = [r["recommendation_id"] for r in recs]
    assert len(set(all_rec_ids)) == 10

    # User state reflects total operations consistently
    state = runtime_service.get_user_state(user_id)
    assert state is not None
    # 1 initial + 10 concurrent = 11 recommendations
    assert state["recommendation_count"] == 11
    # 5 feedback events processed
    assert state["feedback_count"] == 5


# =============================================================================
# Input-Length Consistency & Database Bounded Column Tests (Option A Policy)
# =============================================================================


def test_identifier_maximum_supported_length_success(client, runtime_service):
    """
    Input-Length Verification 1:
    Identifiers at the maximum supported length (exactly 128 characters) succeed:
    - user_id (128 chars)
    - session_id (128 chars)
    - feedback_id (128 chars)
    - preset_id (128 chars)
    Verify no database truncation error occurs and values are preserved exactly.
    """
    max_user_id = "u" * MAX_IDENTIFIER_LENGTH
    max_session_id = "s" * MAX_IDENTIFIER_LENGTH
    max_feedback_id = "f" * MAX_IDENTIFIER_LENGTH
    max_preset_id = PRESET_ENERGETIC_POSITIVE

    assert len(max_user_id) == 128
    assert len(max_session_id) == 128
    assert len(max_feedback_id) == 128

    # 1. Recommendation with 128-char user_id and session_id
    t3 = make_tier3(session_id=max_session_id, seq=0, time_ms=1000)
    rec_res = client.post(
        "/api/personalization/recommend",
        json={"user_id": max_user_id, "tier3_event": t3},
    )
    assert rec_res.status_code == 200, rec_res.text
    rec_data = rec_res.json()
    assert rec_data["session_id"] == max_session_id
    assert len(rec_data["session_id"]) == 128
    # recommendation_id is fixed 36 chars (UUID5), safely <= 128
    assert len(rec_data["recommendation_id"]) == 36
    # Contract v1.1 validation passes
    errors = list(REC_VALIDATOR.iter_errors(rec_data))
    assert len(errors) == 0

    # 2. Feedback with 128-char user_id, session_id, and feedback_id
    fb = make_feedback(
        session_id=max_session_id,
        fb_id=max_feedback_id,
        preset_id=rec_data["recommended_preset_id"],
        fb_type="like",
    )
    fb_res = client.post(
        "/api/personalization/feedback",
        json={"user_id": max_user_id, "feedback_event": fb},
    )
    assert fb_res.status_code == 200, fb_res.text
    fb_data = fb_res.json()
    assert fb_data["status"] == "applied"
    assert fb_data["applied"] is True
    assert fb_data["feedback_id"] == max_feedback_id

    # 3. User state retrieval with 128-char user_id
    state_res = client.get(f"/api/personalization/users/{max_user_id}/state")
    assert state_res.status_code == 200, state_res.text
    state_data = state_res.json()
    assert state_data["user_id"] == max_user_id
    assert len(state_data["user_id"]) == 128
    assert state_data["recommendation_count"] == 1
    assert state_data["feedback_count"] == 1

    # 4. Persistence integrity: verify DB models store exact 128-char values without truncation
    if runtime_service.repository is not None:
        persisted_state = runtime_service.repository.load_user_state(max_user_id)
        assert persisted_state is not None
        assert persisted_state.user_id == max_user_id
        assert len(persisted_state.user_id) == 128

        processed_ids = runtime_service.repository.load_processed_feedback_ids(user_id=max_user_id)
        assert max_feedback_id in processed_ids


def test_identifier_above_maximum_limit_rejected_cleanly(client):
    """
    Input-Length Verification 2:
    Identifiers above the supported limit (129 characters) are rejected cleanly
    with HTTP 422 validation errors before persistence.
    Do not allow PostgreSQL StringDataRightTruncation to occur.
    """
    long_user_id = "u" * (MAX_IDENTIFIER_LENGTH + 1)
    long_session_id = "s" * (MAX_IDENTIFIER_LENGTH + 1)
    long_feedback_id = "f" * (MAX_IDENTIFIER_LENGTH + 1)
    long_preset_id = "p" * (MAX_IDENTIFIER_LENGTH + 1)

    assert len(long_user_id) == 129
    assert len(long_session_id) == 129
    assert len(long_feedback_id) == 129
    assert len(long_preset_id) == 129

    valid_user_id = "user-boundary-test"
    valid_session_id = "sess-boundary-test"

    # 1. RecommendRequest: 129-char user_id rejected with 422
    res1 = client.post(
        "/api/personalization/recommend",
        json={"user_id": long_user_id, "tier3_event": make_tier3(session_id=valid_session_id)},
    )
    assert res1.status_code == 422
    assert "user_id" in res1.text

    # 2. RecommendRequest: 129-char session_id rejected with 422
    res2 = client.post(
        "/api/personalization/recommend",
        json={"user_id": valid_user_id, "tier3_event": make_tier3(session_id=long_session_id)},
    )
    assert res2.status_code == 422
    assert "session_id" in res2.text

    # 3. FeedbackRequest: 129-char user_id rejected with 422
    res3 = client.post(
        "/api/personalization/feedback",
        json={"user_id": long_user_id, "feedback_event": make_feedback(session_id=valid_session_id)},
    )
    assert res3.status_code == 422
    assert "user_id" in res3.text

    # 4. FeedbackRequest: 129-char session_id rejected with 422
    res4 = client.post(
        "/api/personalization/feedback",
        json={"user_id": valid_user_id, "feedback_event": make_feedback(session_id=long_session_id)},
    )
    assert res4.status_code == 422
    assert "session_id" in res4.text

    # 5. FeedbackRequest: 129-char feedback_id rejected with 422
    res5 = client.post(
        "/api/personalization/feedback",
        json={"user_id": valid_user_id, "feedback_event": make_feedback(session_id=valid_session_id, fb_id=long_feedback_id)},
    )
    assert res5.status_code == 422
    assert "feedback_id" in res5.text

    # 6. FeedbackRequest: 129-char preset_id rejected with 422
    res6 = client.post(
        "/api/personalization/feedback",
        json={"user_id": valid_user_id, "feedback_event": make_feedback(session_id=valid_session_id, preset_id=long_preset_id)},
    )
    assert res6.status_code == 422
    assert "preset_id" in res6.text

    # 7. GET user state with 129-char user_id rejected with 422
    res7 = client.get(f"/api/personalization/users/{long_user_id}/state")
    assert res7.status_code == 422


def test_runtime_service_direct_identifier_boundary_validation(runtime_service):
    """
    Input-Length Verification 3:
    Direct callers to PersonalizationRuntimeService receive clean ValueError
    exceptions for identifiers exceeding MAX_IDENTIFIER_LENGTH.
    """
    long_id = "x" * (MAX_IDENTIFIER_LENGTH + 1)
    valid_id = "valid-id"

    # get_engine
    with pytest.raises(ValueError, match="user_id exceeds maximum"):
        runtime_service.get_engine(long_id)

    # recommend user_id
    with pytest.raises(ValueError, match="user_id exceeds maximum"):
        runtime_service.recommend(user_id=long_id, tier3_event=make_tier3())

    # recommend session_id
    with pytest.raises(ValueError, match="session_id exceeds maximum"):
        runtime_service.recommend(user_id=valid_id, tier3_event=make_tier3(session_id=long_id))

    # process_feedback user_id
    with pytest.raises(ValueError, match="user_id exceeds maximum"):
        runtime_service.process_feedback(user_id=long_id, feedback_event=make_feedback())

    # process_feedback session_id
    with pytest.raises(ValueError, match="session_id exceeds maximum"):
        runtime_service.process_feedback(user_id=valid_id, feedback_event=make_feedback(session_id=long_id))

    # process_feedback feedback_id
    with pytest.raises(ValueError, match="feedback_id exceeds maximum"):
        runtime_service.process_feedback(user_id=valid_id, feedback_event=make_feedback(fb_id=long_id))

    # process_feedback preset_id
    with pytest.raises(ValueError, match="preset_id exceeds maximum"):
        runtime_service.process_feedback(user_id=valid_id, feedback_event=make_feedback(preset_id=long_id))

    # persist_user
    with pytest.raises(ValueError, match="user_id exceeds maximum"):
        runtime_service.persist_user(long_id)


def test_database_persistence_identifier_boundaries_no_truncation(in_memory_repo):
    """
    Input-Length Verification 4:
    Verify repository layer guards against column overflow:
    - 128-char identifiers succeed and preserve exact string content without silent truncation.
    - 129-char identifiers are intercepted before persistence and raise ValueError.
    """
    max_id = "k" * MAX_IDENTIFIER_LENGTH
    long_id = "k" * (MAX_IDENTIFIER_LENGTH + 1)

    # 1. 128-char interaction succeeds without truncation
    interaction_128 = {
        "recommendation_id": f"rec_{'a' * 32}",
        "session_id": max_id,
        "recommended_preset_id": PRESET_CALM_POSITIVE,
        "audio_time_ms": 1000,
        "sequence": 0,
        "context_vector": [0.5, -0.5, 1.0],
        "strategy": "cold_start",
        "score": None,
        "feedback_applied": False,
    }
    in_memory_repo.save_interaction(interaction_128, user_id=max_id)

    pending = in_memory_repo.load_pending_interactions(user_id=max_id, session_id=max_id)
    assert len(pending) == 1
    assert pending[0]["session_id"] == max_id
    assert len(pending[0]["session_id"]) == 128  # EXACT length preserved, no truncation

    # 2. 128-char processed feedback succeeds
    saved = in_memory_repo.save_processed_feedback(
        {
            "feedback_id": max_id,
            "session_id": max_id,
            "preset_id": PRESET_CALM_POSITIVE,
            "feedback_type": "like",
            "reward": 1.0,
            "recommendation_id": f"rec_{'a' * 32}",
        },
        user_id=max_id,
    )
    assert saved is True
    assert in_memory_repo.is_feedback_processed(max_id) is True

    # 3. 129-char interaction raises ValueError before DB insert
    bad_interaction = dict(interaction_128)
    bad_interaction["recommendation_id"] = f"rec_{'b' * 32}"
    bad_interaction["session_id"] = long_id
    with pytest.raises(ValueError, match="session_id exceeds maximum"):
        in_memory_repo.save_interaction(bad_interaction, user_id=max_id)

    # 4. 129-char feedback raises ValueError before DB insert
    with pytest.raises(ValueError, match="feedback_id exceeds maximum"):
        in_memory_repo.save_processed_feedback(
            {
                "feedback_id": long_id,
                "session_id": max_id,
                "preset_id": PRESET_CALM_POSITIVE,
                "feedback_type": "like",
            },
            user_id=max_id,
        )


def test_normal_contract_v1_1_flows_remain_unchanged(client):
    """
    Input-Length Verification 5:
    Normal standard Contract v1.1 workflows (standard short identifiers)
    remain completely unchanged and pass all Contract v1.1 validations.
    """
    user_id = "user-standard-flow"
    session_id = "session-standard-01"

    # Step 1: Recommend
    t3 = make_tier3(session_id=session_id, seq=1, time_ms=1000)
    rec_res = client.post(
        "/api/personalization/recommend",
        json={"user_id": user_id, "tier3_event": t3},
    )
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["strategy"] == "cold_start"
    assert rec_data["session_id"] == session_id
    assert list(REC_VALIDATOR.iter_errors(rec_data)) == []

    # Step 2: Feedback
    fb = make_feedback(
        session_id=session_id,
        fb_id="fb-standard-01",
        preset_id=rec_data["recommended_preset_id"],
        fb_type="like",
    )
    fb_res = client.post(
        "/api/personalization/feedback",
        json={"user_id": user_id, "feedback_event": fb},
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["applied"] is True

    # Step 3: Next recommendation uses LinUCB
    t3_next = make_tier3(session_id=session_id, seq=2, time_ms=2000)
    rec_res_next = client.post(
        "/api/personalization/recommend",
        json={"user_id": user_id, "tier3_event": t3_next},
    )
    assert rec_res_next.status_code == 200
    assert rec_res_next.json()["strategy"] == "linucb"
    assert list(REC_VALIDATOR.iter_errors(rec_res_next.json())) == []
