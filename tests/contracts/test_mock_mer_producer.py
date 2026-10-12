import sys
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.mock_mer import create_mock_tier3_event

SCHEMA_PATH = ROOT / "contracts" / "schemas" / "mer-tier3.schema.json"


def test_mock_tier3_producer_conformance():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    validator = Draft202012Validator(schema)
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
        
        # 9. confidence is null
        assert event["emotion"]["confidence"] is None
        
        previous_sequence = event["sequence"]
        previous_audio_time = event["audio_time_ms"]


def test_generation_is_deterministic():
    session_id = "test-session"
    # Calling the generator twice with the same inputs must yield exactly identical output
    event1 = create_mock_tier3_event(session_id, 15, 15000)
    event2 = create_mock_tier3_event(session_id, 15, 15000)
    
    assert event1 == event2
