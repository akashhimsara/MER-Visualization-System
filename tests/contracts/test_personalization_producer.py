import sys
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.personalization import (
    generate_cold_start_recommendation,
    select_cold_start_preset,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_CALM_POSITIVE,
    PRESET_TENSE_NEGATIVE,
    PRESET_CALM_NEGATIVE,
)

SCHEMA_PATH = ROOT / "contracts" / "schemas" / "recommendation.schema.json"


def load_validator() -> Draft202012Validator:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def make_tier3_event(
    valence: float,
    arousal: float,
    session_id: str = "test-session-001",
    sequence: int = 5,
    audio_time_ms: int = 5000,
) -> dict:
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


def test_recommendation_schema_conformance():
    validator = load_validator()
    tier3_event = make_tier3_event(valence=0.7, arousal=0.8, session_id="sess_abc", audio_time_ms=12000)
    rec_seq = 4

    rec = generate_cold_start_recommendation(tier3_event, rec_seq)

    # 1. Passes real Recommendation v1.1 schema
    validator.validate(rec)

    # 2. Schema constants
    assert rec["schema_version"] == "1.1"
    assert rec["event_type"] == "personalization.recommendation"

    # 3. Preserved fields
    assert rec["session_id"] == "sess_abc"
    assert rec["audio_time_ms"] == 12000

    # 4. Independent sequence
    assert rec["sequence"] == 4

    # 5. Deterministic recommendation_id
    assert isinstance(rec["recommendation_id"], str)
    assert len(rec["recommendation_id"]) > 0

    # 6. Cold-start strategy and null score
    assert rec["strategy"] == "cold_start"
    assert rec["score"] is None
    assert rec["recommended_preset_id"] == PRESET_ENERGETIC_POSITIVE


def test_quadrant_mappings():
    validator = load_validator()

    quadrants = [
        # (valence, arousal, expected_preset)
        (0.6, 0.4, PRESET_ENERGETIC_POSITIVE),   # Q1: High Valence, High Arousal
        (0.5, -0.7, PRESET_CALM_POSITIVE),       # Q2: High Valence, Low Arousal
        (-0.6, 0.3, PRESET_TENSE_NEGATIVE),      # Q3: Low Valence, High Arousal
        (-0.4, -0.5, PRESET_CALM_NEGATIVE),      # Q4: Low Valence, Low Arousal
    ]

    for idx, (v, a, expected_preset) in enumerate(quadrants):
        tier3_event = make_tier3_event(valence=v, arousal=a, sequence=idx, audio_time_ms=idx * 1000)
        rec = generate_cold_start_recommendation(tier3_event, idx)
        
        validator.validate(rec)
        assert rec["recommended_preset_id"] == expected_preset
        assert rec["sequence"] == idx
        assert rec["strategy"] == "cold_start"
        assert rec["score"] is None


def test_boundary_values():
    validator = load_validator()

    boundaries = [
        (0.0, 0.0, PRESET_ENERGETIC_POSITIVE),   # Center origin boundary
        (0.0, 0.5, PRESET_ENERGETIC_POSITIVE),   # Zero valence, positive arousal
        (0.0, -0.5, PRESET_CALM_POSITIVE),       # Zero valence, negative arousal
        (0.5, 0.0, PRESET_ENERGETIC_POSITIVE),   # Positive valence, zero arousal
        (-0.5, 0.0, PRESET_TENSE_NEGATIVE),      # Negative valence, zero arousal
        (1.0, 1.0, PRESET_ENERGETIC_POSITIVE),   # Extreme max-max
        (1.0, -1.0, PRESET_CALM_POSITIVE),       # Extreme max-min
        (-1.0, 1.0, PRESET_TENSE_NEGATIVE),      # Extreme min-max
        (-1.0, -1.0, PRESET_CALM_NEGATIVE),      # Extreme min-min
    ]

    for idx, (v, a, expected_preset) in enumerate(boundaries):
        tier3_event = make_tier3_event(valence=v, arousal=a, sequence=idx, audio_time_ms=idx * 500)
        rec = generate_cold_start_recommendation(tier3_event, idx)
        
        validator.validate(rec)
        assert rec["recommended_preset_id"] == expected_preset, f"Failed at ({v}, {a})"
        assert rec["strategy"] == "cold_start"
        assert rec["score"] is None


def test_deterministic_generation():
    tier3_event_a = make_tier3_event(valence=0.35, arousal=-0.25, session_id="det_sess", audio_time_ms=3000)
    tier3_event_b = make_tier3_event(valence=0.35, arousal=-0.25, session_id="det_sess", audio_time_ms=3000)

    rec_a = generate_cold_start_recommendation(tier3_event_a, 10)
    rec_b = generate_cold_start_recommendation(tier3_event_b, 10)

    assert rec_a == rec_b


def test_independent_sequence_advancement():
    validator = load_validator()
    tier3_event = make_tier3_event(valence=0.5, arousal=0.5)

    previous_seq = -1
    for rec_seq in range(10):
        rec = generate_cold_start_recommendation(tier3_event, rec_seq)
        validator.validate(rec)
        assert rec["sequence"] == previous_seq + 1
        previous_seq = rec["sequence"]
