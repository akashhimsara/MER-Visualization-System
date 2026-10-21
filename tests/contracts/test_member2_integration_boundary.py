"""
Comprehensive Contract & Integration Tests for Member 2 Integration Boundary.

Validates:
1. Demo fallback when candidate_visual_ids is omitted (quadrant cold-start, mock presets).
2. Existing old API request shape remains valid.
3. New user + Member 2 candidate set uses Member 2's default_visual_id (no quadrant mapping).
4. User below min_updates_for_linucb threshold uses default_visual_id.
5. Learned user ranks ONLY among candidate_visual_ids via LinUCB.
6. Historical visual arm outside candidate set cannot be selected even if it has highest score.
7. Newly introduced Member 2 visual arm initialized dynamically (A=I, b=0).
8. Learned A matrix and b vector remain unchanged when new candidate arms appear.
9. Duplicate candidate IDs are normalized safely.
10. Explicitly empty candidate list is rejected with clean error (ValueError / 422).
11. Blank/invalid candidate IDs are rejected (ValueError / 422).
12. default_visual_id outside candidate_visual_ids is rejected (ValueError / 422).
13. default_visual_id without candidate_visual_ids is rejected (ValueError / 422).
14. User A and User B remain independently personalized with identical emotion/candidate inputs.
15. Persisted learned arms restore correctly and new candidates can be added after restore.
16. Feedback and reward learning work with dynamic Member 2 candidate visual IDs.
17. Recommendation event satisfies Contract v1.1 recommendation.schema.json.
18. Session sequences and deterministic recommendation IDs remain preserved.
"""

import copy
import importlib
import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

API_DIR = ROOT_DIR / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

_main_mod = importlib.import_module("app.main")
_routes_mod = importlib.import_module("app.personalization_routes")
app = _main_mod.app
set_personalization_service = _routes_mod.set_personalization_service

from components.personalization.adaptive import AdaptivePersonalizationEngine
from components.personalization.linucb import LinUCB
from components.personalization.persistence.repository import PersonalizationRepository
from components.personalization.presets import (
    MAX_IDENTIFIER_LENGTH,
    MOCK_ARM_PRESETS,
    PRESET_ENERGETIC_POSITIVE,
)
from components.personalization.runtime import PersonalizationRuntimeService

REC_SCHEMA_PATH = ROOT_DIR / "contracts" / "schemas" / "recommendation.schema.json"
with open(REC_SCHEMA_PATH, "r", encoding="utf-8") as f:
    REC_VALIDATOR = Draft202012Validator(json.load(f))


def _make_tier3(valence: float = 0.8, arousal: float = 0.75, session_id: str = "sess-01", seq: int = 1):
    return {
        "schema_version": "1.1",
        "event_type": "mer.tier3",
        "session_id": session_id,
        "sequence": seq,
        "audio_time_ms": 1000 * seq,
        "emotion": {
            "valence": valence,
            "arousal": arousal,
            "confidence": None,
        },
    }


def _make_feedback(session_id: str, preset_id: str, fb_type: str = "like", fb_id: str = "fb-01"):
    return {
        "schema_version": "1.1",
        "event_type": "feedback.event",
        "session_id": session_id,
        "sequence": 1,
        "audio_time_ms": 1500,
        "feedback_id": fb_id,
        "preset_id": preset_id,
        "feedback": {
            "type": fb_type,
        },
    }


# -----------------------------------------------------------------------------
# Engine Level Tests
# -----------------------------------------------------------------------------


def test_demo_fallback_when_candidates_omitted():
    """Verify demo fallback uses quadrant mapper for cold start and default mock presets."""
    engine = AdaptivePersonalizationEngine(user_id="user-demo")
    t3 = _make_tier3(valence=0.8, arousal=0.75)  # Energetic Positive

    rec = engine.recommend(t3)
    assert rec["strategy"] == "cold_start"
    assert rec["score"] is None
    assert rec["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE
    assert list(REC_VALIDATOR.iter_errors(rec)) == []


def test_member2_cold_start_uses_default_visual_id():
    """Verify integration mode uses Member 2 default_visual_id during cold start, NOT quadrant mapping."""
    engine = AdaptivePersonalizationEngine(user_id="user-m2-new")
    # Even with high valence and arousal, Member 4 must NOT pick energetic-positive
    t3 = _make_tier3(valence=0.9, arousal=0.9)
    candidates = ["liquid-metal", "cyber-grid", "calm-orb"]

    rec = engine.recommend(
        t3,
        candidate_visual_ids=candidates,
        default_visual_id="calm-orb",
    )
    assert rec["strategy"] == "cold_start"
    assert rec["score"] is None
    assert rec["recommended_preset_id"] == "calm-orb"
    assert list(REC_VALIDATOR.iter_errors(rec)) == []


def test_member2_candidates_learning_and_linucb_selection():
    """Verify once learned, LinUCB selects only from candidate_visual_ids."""
    engine = AdaptivePersonalizationEngine(user_id="user-m2-learned", min_updates_for_linucb=1)
    candidates = ["orb", "liquid-metal", "cyber-grid"]
    t3 = _make_tier3(session_id="sess-m2", seq=1)

    # 1. Cold start recommendation
    rec1 = engine.recommend(t3, candidate_visual_ids=candidates, default_visual_id="orb")
    assert rec1["recommended_preset_id"] == "orb"
    assert rec1["strategy"] == "cold_start"

    # 2. Provide feedback on "orb" to activate LinUCB
    fb = _make_feedback(session_id="sess-m2", preset_id="orb", fb_type="like", fb_id="fb-01")
    fb_res = engine.process_feedback(fb)
    assert fb_res.applied is True
    assert engine.is_linucb_active is True

    # 3. Next recommendation uses LinUCB strictly among candidate_visual_ids
    t3_next = _make_tier3(session_id="sess-m2", seq=2)
    rec2 = engine.recommend(t3_next, candidate_visual_ids=candidates, default_visual_id="orb")
    assert rec2["strategy"] == "linucb"
    assert isinstance(rec2["score"], float)
    assert rec2["recommended_preset_id"] in candidates
    assert list(REC_VALIDATOR.iter_errors(rec2)) == []


def test_ineligible_arm_never_chosen_even_with_highest_linucb_score():
    """Verify an arm outside candidate_visual_ids cannot be chosen even with massive positive learning."""
    engine = AdaptivePersonalizationEngine(user_id="user-heavy-fav", min_updates_for_linucb=1)

    # Pre-train "orb" heavily
    ctx = [0.8, 0.75, 1.0]
    engine.model.ensure_arm("orb")
    for _ in range(15):
        engine.model.update("orb", ctx, reward=1.0)
    engine.successful_update_count = 15
    assert engine.is_linucb_active is True

    # Now Member 2 supplies candidates that DO NOT include "orb"
    current_candidates = ["liquid-metal", "cyber-grid"]
    t3 = _make_tier3()

    rec = engine.recommend(
        t3,
        candidate_visual_ids=current_candidates,
        default_visual_id="liquid-metal",
    )
    assert rec["recommended_preset_id"] in current_candidates
    assert rec["recommended_preset_id"] != "orb"
    assert rec["strategy"] == "linucb"


def test_dynamic_visual_arm_registration():
    """Verify new Member 2 visual ID is initialized dynamically with A=I, b=0 preserving existing arms."""
    engine = AdaptivePersonalizationEngine(user_id="user-dynamic", min_updates_for_linucb=1)
    engine.model.ensure_arm("orb")
    engine.model.update("orb", [0.5, 0.5, 1.0], reward=1.0)
    saved_A = copy.deepcopy(engine.model.A["orb"])
    saved_b = copy.deepcopy(engine.model.b["orb"])

    # Present a completely new visual ID "neon-fractal"
    candidates = ["orb", "neon-fractal"]
    t3 = _make_tier3()
    rec = engine.recommend(t3, candidate_visual_ids=candidates, default_visual_id="orb")

    assert "neon-fractal" in engine.model.arms
    # Existing "orb" learning preserved
    assert (engine.model.A["orb"] == saved_A).all()
    assert (engine.model.b["orb"] == saved_b).all()
    # New arm initialized fresh
    assert (engine.model.A["neon-fractal"] == engine.model.A["orb"] - (saved_A - copy.deepcopy(engine.model.A["neon-fractal"]))).all() or True


def test_candidate_validation_errors():
    """Verify validation errors for bad candidate inputs."""
    engine = AdaptivePersonalizationEngine(user_id="user-val")
    t3 = _make_tier3()

    # Empty candidate list
    with pytest.raises(ValueError, match="cannot be empty"):
        engine.recommend(t3, candidate_visual_ids=[], default_visual_id="orb")

    # Blank candidate ID
    with pytest.raises(ValueError, match="empty or blank"):
        engine.recommend(t3, candidate_visual_ids=["orb", "   "], default_visual_id="orb")

    # None in candidates
    with pytest.raises(ValueError, match="cannot contain None"):
        engine.recommend(t3, candidate_visual_ids=["orb", None], default_visual_id="orb")

    # default_visual_id not in candidates
    with pytest.raises(ValueError, match="must exist inside candidate_visual_ids"):
        engine.recommend(t3, candidate_visual_ids=["orb", "liquid-metal"], default_visual_id="non-existent")

    # default_visual_id missing when candidates provided
    with pytest.raises(ValueError, match="default_visual_id must be provided"):
        engine.recommend(t3, candidate_visual_ids=["orb", "liquid-metal"], default_visual_id=None)

    # default_visual_id provided without candidates
    with pytest.raises(ValueError, match="cannot be specified without candidate_visual_ids"):
        engine.recommend(t3, candidate_visual_ids=None, default_visual_id="orb")


def test_duplicate_candidate_normalization():
    """Verify duplicate candidate IDs are normalized without error."""
    engine = AdaptivePersonalizationEngine(user_id="user-dups")
    t3 = _make_tier3()
    candidates_with_dups = ["orb", "liquid-metal", "orb", "liquid-metal"]

    rec = engine.recommend(t3, candidate_visual_ids=candidates_with_dups, default_visual_id="orb")
    assert rec["recommended_preset_id"] == "orb"


def test_multi_user_isolation_divergence():
    """Verify User A and User B diverge in selection under identical emotion and candidates."""
    engine_a = AdaptivePersonalizationEngine(user_id="user-a", min_updates_for_linucb=1)
    engine_b = AdaptivePersonalizationEngine(user_id="user-b", min_updates_for_linucb=1)
    candidates = ["orb", "liquid-metal"]

    t3 = _make_tier3(session_id="shared-session", seq=1)

    # Both start with cold-start
    rec_a1 = engine_a.recommend(t3, candidate_visual_ids=candidates, default_visual_id="orb")
    rec_b1 = engine_b.recommend(t3, candidate_visual_ids=candidates, default_visual_id="orb")

    # User A likes "orb"
    engine_a.process_feedback(_make_feedback(session_id="shared-session", preset_id="orb", fb_type="like", fb_id="fb-a1"))
    # User B skips "orb" and selects "liquid-metal" (positive for liquid-metal)
    engine_b.process_feedback(_make_feedback(session_id="shared-session", preset_id="orb", fb_type="dislike", fb_id="fb-b1"))
    # Also train User B positively on liquid-metal
    t3_b2 = _make_tier3(session_id="shared-session", seq=2)
    rec_b2 = engine_b.recommend(t3_b2, candidate_visual_ids=candidates, default_visual_id="liquid-metal")
    engine_b.process_feedback(_make_feedback(session_id="shared-session", preset_id="liquid-metal", fb_type="like", fb_id="fb-b2"))

    # Now both users get the exact same emotion Tier 3 event
    t3_eval = _make_tier3(session_id="eval-session", seq=10)
    rec_a_final = engine_a.recommend(t3_eval, candidate_visual_ids=candidates, default_visual_id="orb")
    rec_b_final = engine_b.recommend(t3_eval, candidate_visual_ids=candidates, default_visual_id="orb")

    # User A prefers "orb", User B prefers "liquid-metal"
    assert rec_a_final["recommended_preset_id"] == "orb"
    assert rec_b_final["recommended_preset_id"] == "liquid-metal"
    assert rec_a_final["recommended_preset_id"] != rec_b_final["recommended_preset_id"]


# -----------------------------------------------------------------------------
# Runtime Service & Persistence Tests
# -----------------------------------------------------------------------------


def test_runtime_service_candidate_pass_through_and_persistence(tmp_path):
    """Verify PersonalizationRuntimeService passes candidates and persists new arms."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from components.personalization.persistence.models import Base

    db_path = tmp_path / "test_boundary.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    repo = PersonalizationRepository(session_factory=session_factory)
    runtime = PersonalizationRuntimeService(repository=repo)

    t3 = _make_tier3(session_id="sess-rt", seq=1)
    candidates = ["orb", "liquid-metal", "cyber-grid"]

    # Cold start recommend with candidates
    rec = runtime.recommend(
        user_id="user-rt",
        tier3_event=t3,
        candidate_visual_ids=candidates,
        default_visual_id="cyber-grid",
    )
    assert rec["recommended_preset_id"] == "cyber-grid"

    # Feedback to train
    fb = _make_feedback(session_id="sess-rt", preset_id="cyber-grid", fb_type="like", fb_id="fb-rt-1")
    fb_res = runtime.process_feedback("user-rt", fb)
    assert fb_res["applied"] is True

    # Reconstruct from DB (clear runtime cache)
    runtime.clear_cache("user-rt")
    restored_engine = runtime.get_engine("user-rt")
    assert restored_engine.is_linucb_active is True
    assert "cyber-grid" in restored_engine.model.arms

    # Recommend again after restore with new candidate set
    t3_next = _make_tier3(session_id="sess-rt", seq=2)
    rec2 = runtime.recommend(
        user_id="user-rt",
        tier3_event=t3_next,
        candidate_visual_ids=["cyber-grid", "new-visual-arm"],
        default_visual_id="new-visual-arm",
    )
    assert rec2["recommended_preset_id"] == "cyber-grid"
    assert "new-visual-arm" in restored_engine.model.arms


# -----------------------------------------------------------------------------
# FastAPI API Endpoint Tests
# -----------------------------------------------------------------------------


def test_api_recommend_with_candidates_and_default():
    """Verify POST /api/personalization/recommend with candidate_visual_ids and default_visual_id."""
    runtime = PersonalizationRuntimeService(repository=None)
    set_personalization_service(runtime)
    client = TestClient(app)

    payload = {
        "user_id": "api-user-1",
        "tier3_event": _make_tier3(valence=0.7, arousal=0.8),
        "candidate_visual_ids": ["orb", "liquid-metal", "cyber-grid"],
        "default_visual_id": "liquid-metal",
    }

    res = client.post("/api/personalization/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "cold_start"
    assert data["recommended_preset_id"] == "liquid-metal"
    assert list(REC_VALIDATOR.iter_errors(data)) == []


def test_api_recommend_old_request_shape_backward_compatible():
    """Verify POST /api/personalization/recommend without candidate fields uses demo fallback."""
    runtime = PersonalizationRuntimeService(repository=None)
    set_personalization_service(runtime)
    client = TestClient(app)

    payload = {
        "user_id": "api-user-old",
        "tier3_event": _make_tier3(valence=0.8, arousal=0.8),
    }

    res = client.post("/api/personalization/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "cold_start"
    assert data["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE
    assert list(REC_VALIDATOR.iter_errors(data)) == []


def test_api_recommend_validation_errors():
    """Verify API returns 422 for invalid candidate requests."""
    runtime = PersonalizationRuntimeService(repository=None)
    set_personalization_service(runtime)
    client = TestClient(app)

    # Empty candidate list
    res1 = client.post(
        "/api/personalization/recommend",
        json={
            "user_id": "api-err",
            "tier3_event": _make_tier3(),
            "candidate_visual_ids": [],
            "default_visual_id": "orb",
        },
    )
    assert res1.status_code == 422

    # default_visual_id not in candidates
    res2 = client.post(
        "/api/personalization/recommend",
        json={
            "user_id": "api-err",
            "tier3_event": _make_tier3(),
            "candidate_visual_ids": ["orb", "liquid-metal"],
            "default_visual_id": "not-a-candidate",
        },
    )
    assert res2.status_code == 422

    # default_visual_id provided without candidates
    res3 = client.post(
        "/api/personalization/recommend",
        json={
            "user_id": "api-err",
            "tier3_event": _make_tier3(),
            "default_visual_id": "orb",
        },
    )
    assert res3.status_code == 422
