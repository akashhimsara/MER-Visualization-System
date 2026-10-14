import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    calculate_reward,
    normalize_rating,
    RewardResult,
    REWARD_LIKE,
    REWARD_DISLIKE,
    REWARD_PRESET_SELECT,
    REWARD_PRESET_SKIP,
    REWARD_VIEW_DURATION,
)

SCHEMA_PATH = ROOT / "contracts" / "schemas" / "feedback-event.schema.json"


def load_validator() -> Draft202012Validator:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def make_feedback_event(
    feedback_type: str,
    rating: Optional[int] = None,
    duration_ms: Optional[int] = None,
    preset_id: str = "neon_tunnel_warm_01",
    session_id: str = "sess_demo_001",
    sequence: int = 1,
    audio_time_ms: int = 1000,
    feedback_id: str = "fb_001",
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


def test_like_reward():
    validator = load_validator()
    event = make_feedback_event("like")
    validator.validate(event)

    result = calculate_reward(event)
    assert result["reward"] == 1.0
    assert result.reward == 1.0
    assert result["feedback_type"] == "like"
    assert result["is_explicit"] is True
    assert result["is_auxiliary"] is False
    assert result["preset_id"] == "neon_tunnel_warm_01"
    assert result["session_id"] == "sess_demo_001"


def test_dislike_reward():
    validator = load_validator()
    event = make_feedback_event("dislike")
    validator.validate(event)

    result = calculate_reward(event)
    assert result["reward"] == -1.0
    assert result.reward == -1.0
    assert result["feedback_type"] == "dislike"
    assert result["is_explicit"] is True
    assert result["is_auxiliary"] is False


def test_rating_normalization_all_values():
    validator = load_validator()
    expected_mappings = {
        1: -1.0,
        2: -0.5,
        3: 0.0,
        4: +0.5,
        5: +1.0,
    }

    for rating_val, expected_reward in expected_mappings.items():
        event = make_feedback_event("rating", rating=rating_val)
        validator.validate(event)

        result = calculate_reward(event)
        assert result["reward"] == expected_reward, f"Failed for rating {rating_val}"
        assert result.reward == expected_reward
        assert result["feedback_type"] == "rating"
        assert result["is_explicit"] is True
        assert result["is_auxiliary"] is False
        assert result["raw_value"] == rating_val


def test_preset_select_reward():
    validator = load_validator()
    event = make_feedback_event("preset_select")
    validator.validate(event)

    result = calculate_reward(event)
    assert result["reward"] == 0.75
    assert result.reward == 0.75
    assert result["feedback_type"] == "preset_select"
    assert result["is_explicit"] is False
    assert result["is_auxiliary"] is False


def test_preset_skip_reward():
    validator = load_validator()
    event = make_feedback_event("preset_skip")
    validator.validate(event)

    result = calculate_reward(event)
    assert result["reward"] == -0.75
    assert result.reward == -0.75
    assert result["feedback_type"] == "preset_skip"
    assert result["is_explicit"] is False
    assert result["is_auxiliary"] is False


def test_view_duration_deferred_reward():
    validator = load_validator()
    event = make_feedback_event("view_duration", duration_ms=25000)
    validator.validate(event)

    result = calculate_reward(event)
    assert result["reward"] is None
    assert result.reward is None
    assert result["feedback_type"] == "view_duration"
    assert result["is_explicit"] is False
    assert result["is_auxiliary"] is True
    assert result["raw_value"] == 25000


def test_deterministic_behaviour():
    validator = load_validator()
    event = make_feedback_event("rating", rating=4, sequence=12, audio_time_ms=12000)
    validator.validate(event)

    res1 = calculate_reward(event)
    res2 = calculate_reward(event)

    assert res1 == res2
    assert res1.reward == res2.reward == 0.5


def test_reward_result_dict_and_attribute_access():
    event = make_feedback_event("like", preset_id="preset_99", session_id="sess_42", feedback_id="fb_99")
    res = calculate_reward(event)

    assert isinstance(res, dict)
    assert isinstance(res, RewardResult)
    assert res["reward"] == res.reward == 1.0
    assert res["preset_id"] == res.preset_id == "preset_99"
    assert res["session_id"] == res.session_id == "sess_42"
    assert res["feedback_id"] == res.feedback_id == "fb_99"
