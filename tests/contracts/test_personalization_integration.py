import sys
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.mock_mer import MockMERScheduler
from components.personalization import select_cold_start_preset

REC_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "recommendation.schema.json"
TIER3_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "mer-tier3.schema.json"


def load_validator(path: Path) -> Draft202012Validator:
    with open(path, "r", encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


def test_multiplexed_scheduler_emits_one_recommendation_per_tier3():
    rec_validator = load_validator(REC_SCHEMA_PATH)
    tier3_validator = load_validator(TIER3_SCHEMA_PATH)

    session_id = "test-multiplexed-session"
    scheduler = MockMERScheduler(session_id=session_id, step_interval_ms=100)

    tier3_events = []
    rec_events = []

    # Simulate 61 ticks (0 to 6000 ms)
    for tick_idx in range(61):
        tick_events = scheduler.tick()

        t3_in_tick = [e for e in tick_events if e["event_type"] == "mer.tier3"]
        rec_in_tick = [e for e in tick_events if e["event_type"] == "personalization.recommendation"]

        # Exactly 1 recommendation per Tier3 event
        if tick_idx % 10 == 0:
            assert len(t3_in_tick) == 1, f"Expected 1 Tier3 at tick {tick_idx}"
            assert len(rec_in_tick) == 1, f"Expected 1 Recommendation at tick {tick_idx}"

            t3 = t3_in_tick[0]
            rec = rec_in_tick[0]

            # Validate schemas
            tier3_validator.validate(t3)
            rec_validator.validate(rec)

            # Check preserved session_id & audio_time_ms
            assert rec["session_id"] == session_id
            assert rec["session_id"] == t3["session_id"]
            assert rec["audio_time_ms"] == t3["audio_time_ms"]

            # Strategy & score requirements
            assert rec["strategy"] == "cold_start"
            assert rec["score"] is None
            assert rec["schema_version"] == "1.1"

            # Check policy matching
            expected_preset = select_cold_start_preset(
                t3["emotion"]["valence"],
                t3["emotion"]["arousal"],
            )
            assert rec["recommended_preset_id"] == expected_preset

            # Deterministic recommendation_id check
            assert rec["recommendation_id"] == f"rec_{session_id}_{rec['sequence']}"

            tier3_events.append(t3)
            rec_events.append(rec)
        else:
            assert len(t3_in_tick) == 0, f"Unexpected Tier3 at tick {tick_idx}"
            assert len(rec_in_tick) == 0, f"Unexpected Recommendation at tick {tick_idx}"

    # Verify overall event counts
    assert len(tier3_events) == 7
    assert len(rec_events) == 7

    # Verify independent sequence advancement
    assert [e["sequence"] for e in rec_events] == list(range(7))
    assert [e["sequence"] for e in tier3_events] == list(range(7))


def test_multiplexed_recommendation_determinism():
    session_id = "test-deterministic-session"
    sched_a = MockMERScheduler(session_id=session_id, step_interval_ms=100)
    sched_b = MockMERScheduler(session_id=session_id, step_interval_ms=100)

    for _ in range(35):
        events_a = sched_a.tick()
        events_b = sched_b.tick()
        assert events_a == events_b


def test_independent_recommendation_sequence_across_ticks():
    validator = load_validator(REC_SCHEMA_PATH)
    session_id = "test-seq-session"
    scheduler = MockMERScheduler(session_id=session_id, step_interval_ms=100)

    expected_rec_seq = 0
    # Simulate 101 ticks (11 Tier3 and 11 Recommendation events)
    for _ in range(101):
        tick_events = scheduler.tick()
        recs = [e for e in tick_events if e["event_type"] == "personalization.recommendation"]
        for rec in recs:
            validator.validate(rec)
            assert rec["sequence"] == expected_rec_seq
            expected_rec_seq += 1

    assert expected_rec_seq == 11
