import sys
import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    build_context_vector,
    ContextVector,
    FEATURE_NAMES,
    CONTEXT_DIMENSION,
    DEFAULT_BIAS_TERM,
)

TIER3_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "mer-tier3.schema.json"


def load_tier3_validator() -> Draft202012Validator:
    with open(TIER3_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def make_tier3_event(
    valence: float,
    arousal: float,
    session_id: str = "sess_demo_001",
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


def test_feature_order_and_dimension():
    validator = load_tier3_validator()
    event = make_tier3_event(valence=0.65, arousal=-0.20)
    validator.validate(event)

    result = build_context_vector(event)

    # 1. Feature order
    assert result["feature_names"] == ["valence", "arousal", "bias"]
    assert result.feature_names == ["valence", "arousal", "bias"]
    assert result.feature_names == FEATURE_NAMES

    # 2. Vector dimension
    assert result["dimension"] == 3
    assert result.dimension == 3
    assert result.dimension == CONTEXT_DIMENSION
    assert len(result["values"]) == 3
    assert len(result.vector) == 3
    assert len(result.vector_values) == 3


def test_exact_value_preservation():
    validator = load_tier3_validator()
    test_valence = 0.65
    test_arousal = -0.20
    event = make_tier3_event(valence=test_valence, arousal=test_arousal)
    validator.validate(event)

    result = build_context_vector(event)

    assert result["values"] == [0.65, -0.20, 1.0]
    assert result.vector == [0.65, -0.20, 1.0]
    assert result.vector_values == [0.65, -0.20, 1.0]
    assert result.valence == test_valence
    assert result.arousal == test_arousal
    assert result.bias == 1.0
    assert result.bias == DEFAULT_BIAS_TERM
    assert result.to_list() == [0.65, -0.20, 1.0]


def test_boundary_values():
    validator = load_tier3_validator()
    boundary_points = [
        (-1.0, -1.0),
        (-1.0, 0.0),
        (-1.0, 1.0),
        (0.0, -1.0),
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, -1.0),
        (1.0, 0.0),
        (1.0, 1.0),
    ]

    for val, aro in boundary_points:
        event = make_tier3_event(valence=val, arousal=aro)
        validator.validate(event)

        result = build_context_vector(event)
        assert result.dimension == 3
        assert result.valence == val
        assert result.arousal == aro
        assert result.bias == 1.0
        assert result["values"] == [val, aro, 1.0]
        assert result.vector == [val, aro, 1.0]
        assert result.vector_values == [val, aro, 1.0]


def test_determinism():
    validator = load_tier3_validator()
    event = make_tier3_event(valence=0.42, arousal=-0.73)
    validator.validate(event)

    vec1 = build_context_vector(event)
    vec2 = build_context_vector(event)

    assert vec1 == vec2
    assert vec1["values"] == vec2["values"]
    assert vec1.vector == vec2.vector
    assert vec1.vector_values == vec2.vector_values
    assert vec1.to_list() == vec2.to_list()


def test_changing_valence_only_changes_valence():
    validator = load_tier3_validator()
    fixed_arousal = -0.40

    event_a = make_tier3_event(valence=0.20, arousal=fixed_arousal)
    event_b = make_tier3_event(valence=0.80, arousal=fixed_arousal)
    validator.validate(event_a)
    validator.validate(event_b)

    vec_a = build_context_vector(event_a)
    vec_b = build_context_vector(event_b)

    # Valence changes
    assert vec_a.valence == 0.20
    assert vec_b.valence == 0.80
    assert vec_a["values"][0] != vec_b["values"][0]
    assert vec_a.vector[0] != vec_b.vector[0]

    # Arousal and bias remain strictly identical
    assert vec_a.arousal == vec_b.arousal == fixed_arousal
    assert vec_a["values"][1] == vec_b["values"][1] == fixed_arousal
    assert vec_a.vector[1] == vec_b.vector[1] == fixed_arousal
    assert vec_a.bias == vec_b.bias == 1.0
    assert vec_a["values"][2] == vec_b["values"][2] == 1.0
    assert vec_a.vector[2] == vec_b.vector[2] == 1.0


def test_changing_arousal_only_changes_arousal():
    validator = load_tier3_validator()
    fixed_valence = 0.50

    event_a = make_tier3_event(valence=fixed_valence, arousal=-0.30)
    event_b = make_tier3_event(valence=fixed_valence, arousal=0.70)
    validator.validate(event_a)
    validator.validate(event_b)

    vec_a = build_context_vector(event_a)
    vec_b = build_context_vector(event_b)

    # Arousal changes
    assert vec_a.arousal == -0.30
    assert vec_b.arousal == 0.70
    assert vec_a["values"][1] != vec_b["values"][1]
    assert vec_a.vector[1] != vec_b.vector[1]

    # Valence and bias remain strictly identical
    assert vec_a.valence == vec_b.valence == fixed_valence
    assert vec_a["values"][0] == vec_b["values"][0] == fixed_valence
    assert vec_a.vector[0] == vec_b.vector[0] == fixed_valence
    assert vec_a.bias == vec_b.bias == 1.0
    assert vec_a["values"][2] == vec_b["values"][2] == 1.0
    assert vec_a.vector[2] == vec_b.vector[2] == 1.0


def test_context_vector_dict_and_attribute_access():
    event = make_tier3_event(valence=0.1, arousal=0.2)
    res = build_context_vector(event)

    assert isinstance(res, dict)
    assert isinstance(res, ContextVector)
    assert res["dimension"] == res.dimension == 3
    assert res["feature_names"] == res.feature_names == ["valence", "arousal", "bias"]
    assert res["values"] == res.vector == res.vector_values == [0.1, 0.2, 1.0]
    assert res.to_list() == [0.1, 0.2, 1.0]

    # Verify that built-in dict.values() method is NOT shadowed and returns dict values view
    dict_values_list = list(res.values())
    assert ["valence", "arousal", "bias"] in dict_values_list
    assert [0.1, 0.2, 1.0] in dict_values_list
    assert 3 in dict_values_list
