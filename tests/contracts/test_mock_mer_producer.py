import sys
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.mock_mer import (
    create_mock_tier1_event,
    create_mock_tier2_event,
    create_mock_tier3_event,
    MockMERScheduler,
)

SCHEMA_DIR = ROOT / "contracts" / "schemas"
TIER1_SCHEMA_PATH = SCHEMA_DIR / "mer-tier1.schema.json"
TIER2_SCHEMA_PATH = SCHEMA_DIR / "mer-tier2.schema.json"
TIER3_SCHEMA_PATH = SCHEMA_DIR / "mer-tier3.schema.json"


def load_validator(schema_path: Path) -> Draft202012Validator:
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def test_mock_tier1_producer_conformance():
    validator = load_validator(TIER1_SCHEMA_PATH)
    session_id = "test-mock-session-001"
    
    previous_sequence = -1
    previous_audio_time = -100
    
    for _ in range(15):
        expected_seq = previous_sequence + 1
        expected_audio_time = previous_audio_time + 100
        
        event = create_mock_tier1_event(session_id, expected_seq, expected_audio_time)
        
        # 1. Satisfies mer-tier1.schema.json
        validator.validate(event)
        
        # 2. Envelope constants
        assert event["schema_version"] == "1.1"
        assert event["event_type"] == "mer.tier1"
        assert event["session_id"] == session_id
        assert len(event["session_id"]) > 0
        
        # 3. Independent sequence & audio time
        assert event["sequence"] == expected_seq
        assert event["audio_time_ms"] == expected_audio_time
        
        # 4. Values inside contract ranges
        assert 0.0 <= event["rms"] <= 1.0
        assert event["spectral_centroid_hz"] >= 0.0
        assert isinstance(event["onset"]["detected"], bool)
        if event["onset"]["strength"] is not None:
            assert 0.0 <= event["onset"]["strength"] <= 1.0
            
        if event.get("beat") is not None:
            assert isinstance(event["beat"]["detected"], bool)
            if event["beat"]["strength"] is not None:
                assert 0.0 <= event["beat"]["strength"] <= 1.0
        
        previous_sequence = event["sequence"]
        previous_audio_time = event["audio_time_ms"]


def test_mock_tier2_producer_conformance():
    validator = load_validator(TIER2_SCHEMA_PATH)
    session_id = "test-mock-session-001"
    
    previous_sequence = -1
    previous_audio_time = -3000
    
    for _ in range(10):
        expected_seq = previous_sequence + 1
        expected_audio_time = previous_audio_time + 3000
        
        event = create_mock_tier2_event(session_id, expected_seq, expected_audio_time)
        
        # 1. Satisfies mer-tier2.schema.json
        validator.validate(event)
        
        # 2. Envelope constants
        assert event["schema_version"] == "1.1"
        assert event["event_type"] == "mer.tier2"
        assert event["session_id"] == session_id
        assert len(event["session_id"]) > 0
        
        # 3. Independent sequence & audio time
        assert event["sequence"] == expected_seq
        assert event["audio_time_ms"] == expected_audio_time
        
        # 4. Values inside contract ranges
        assert event["tempo_bpm"] > 0
        if event["tempo_confidence"] is not None:
            assert 0.0 <= event["tempo_confidence"] <= 1.0
            
        previous_sequence = event["sequence"]
        previous_audio_time = event["audio_time_ms"]


def test_mock_tier3_producer_conformance():
    validator = load_validator(TIER3_SCHEMA_PATH)
    session_id = "test-mock-session-001"
    
    previous_sequence = -1
    previous_audio_time = -1000
    
    # Validate 10 sequential events
    for _ in range(10):
        expected_seq = previous_sequence + 1
        expected_audio_time = previous_audio_time + 1000
        
        event = create_mock_tier3_event(session_id, expected_seq, expected_audio_time)
        
        # 1. Satisfies mer-tier3.schema.json
        validator.validate(event)
        
        # 2. schema_version == "1.1"
        assert event["schema_version"] == "1.1"
        
        # 3. event_type == "mer.tier3"
        assert event["event_type"] == "mer.tier3"
        
        # 4. session_id is non-empty
        assert event["session_id"] == session_id
        assert len(event["session_id"]) > 0
        
        # 5. sequence increments exactly by 1
        assert event["sequence"] == expected_seq
        
        # 6. audio_time_ms increments exactly by 1000
        assert event["audio_time_ms"] == expected_audio_time
        
        # 7. valence in [-1.0, 1.0]
        valence = event["emotion"]["valence"]
        assert -1.0 <= valence <= 1.0
        
        # 8. arousal in [-1.0, 1.0]
        arousal = event["emotion"]["arousal"]
        assert -1.0 <= arousal <= 1.0
        
        # 9. confidence is null for mock data
        assert event["emotion"]["confidence"] is None
        
        previous_sequence = event["sequence"]
        previous_audio_time = event["audio_time_ms"]


def test_generation_is_deterministic():
    session_id = "test-session"
    
    # Tier 1 determinism
    t1_a = create_mock_tier1_event(session_id, 15, 1500)
    t1_b = create_mock_tier1_event(session_id, 15, 1500)
    assert t1_a == t1_b
    
    # Tier 2 determinism
    t2_a = create_mock_tier2_event(session_id, 5, 15000)
    t2_b = create_mock_tier2_event(session_id, 5, 15000)
    assert t2_a == t2_b
    
    # Tier 3 determinism
    t3_a = create_mock_tier3_event(session_id, 15, 15000)
    t3_b = create_mock_tier3_event(session_id, 15, 15000)
    assert t3_a == t3_b


def test_mock_mer_scheduler_cadence_and_independence():
    validator1 = load_validator(TIER1_SCHEMA_PATH)
    validator2 = load_validator(TIER2_SCHEMA_PATH)
    validator3 = load_validator(TIER3_SCHEMA_PATH)
    
    session_id = "scheduler-mock-session"
    scheduler = MockMERScheduler(session_id=session_id, step_interval_ms=100)
    
    tier1_events = []
    tier2_events = []
    tier3_events = []
    
    # Simulate 61 ticks (0 to 6000 ms inclusive)
    for tick_idx in range(61):
        tick_events = scheduler.tick()
        assert len(tick_events) >= 1  # Tier 1 always emitted
        
        # Check cadences for this tick
        event_types = [e["event_type"] for e in tick_events]
        assert "mer.tier1" in event_types
        
        if tick_idx % 10 == 0:
            assert "mer.tier3" in event_types
        else:
            assert "mer.tier3" not in event_types
            
        if tick_idx % 30 == 0:
            assert "mer.tier2" in event_types
        else:
            assert "mer.tier2" not in event_types
            
        for e in tick_events:
            assert e["session_id"] == session_id
            if e["event_type"] == "mer.tier1":
                validator1.validate(e)
                tier1_events.append(e)
            elif e["event_type"] == "mer.tier2":
                validator2.validate(e)
                tier2_events.append(e)
            elif e["event_type"] == "mer.tier3":
                validator3.validate(e)
                tier3_events.append(e)

    # 1. Check counts
    assert len(tier1_events) == 61
    assert len(tier3_events) == 7   # 0, 1000, 2000, 3000, 4000, 5000, 6000 ms
    assert len(tier2_events) == 3   # 0, 3000, 6000 ms

    # 2. Check independent sequence counters
    assert [e["sequence"] for e in tier1_events] == list(range(61))
    assert [e["sequence"] for e in tier3_events] == list(range(7))
    assert [e["sequence"] for e in tier2_events] == list(range(3))

    # 3. Check audio_time_ms
    assert [e["audio_time_ms"] for e in tier1_events] == [i * 100 for i in range(61)]
    assert [e["audio_time_ms"] for e in tier3_events] == [0, 1000, 2000, 3000, 4000, 5000, 6000]
    assert [e["audio_time_ms"] for e in tier2_events] == [0, 3000, 6000]
