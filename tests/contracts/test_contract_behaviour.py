import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "contracts" / "schemas"
EXAMPLE_DIR = ROOT / "contracts" / "examples"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def schema(name: str):
    return load_json(SCHEMA_DIR / f"{name}.schema.json")


def example(name: str):
    return load_json(EXAMPLE_DIR / f"{name}.example.json")


def is_valid(schema_data, instance):
    return Draft202012Validator(schema_data).is_valid(instance)


def test_mer_tier3_rejects_out_of_range_valence():
    data = example("mer-tier3")
    data["emotion"]["valence"] = 5

    assert not is_valid(schema("mer-tier3"), data)


def test_feedback_rating_requires_rating_value():
    data = example("feedback-event")
    data["feedback"] = {
        "type": "rating"
    }

    assert not is_valid(schema("feedback-event"), data)


def test_feedback_rating_accepts_valid_rating():
    data = example("feedback-event")
    data["feedback"] = {
        "type": "rating",
        "rating": 4
    }

    assert is_valid(schema("feedback-event"), data)


def test_view_duration_requires_duration_ms():
    data = example("feedback-event")
    data["feedback"] = {
        "type": "view_duration"
    }

    assert not is_valid(schema("feedback-event"), data)


def test_transition_false_rejects_transition_payload():
    data = example("transition-command")

    data["should_transition"] = False
    data["target_state_id"] = "state_001"

    assert not is_valid(schema("transition-command"), data)


def test_transition_false_accepts_null_target_and_transition():
    data = example("transition-command")

    data["should_transition"] = False
    data["target_state_id"] = None
    data["transition"] = None

    assert is_valid(schema("transition-command"), data)


def test_strict_contract_rejects_unexpected_top_level_field():
    data = example("mer-tier3")
    data["unexpected_field"] = "test"

    assert not is_valid(schema("mer-tier3"), data)
