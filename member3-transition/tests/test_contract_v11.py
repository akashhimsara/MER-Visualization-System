import json
 
import jsonschema
 
from src.contract.demo_v11 import SCHEMA, simulated_stream
from src.contract.engine_v11 import ContractTransitionEngine, REPO_ROOT
 
VALIDATOR = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
 
 
def _run(rows):
    engine = ContractTransitionEngine("sess_test")
    return [c for c in (engine.process_tier3(*r) for r in rows) if c]
 
 
def test_all_commands_match_schema():
    cmds = _run(simulated_stream())
    assert cmds
    for c in cmds:
        VALIDATOR.validate(c)
 
 
def test_demo_stream_produces_transitions():
    fired = [c for c in _run(simulated_stream()) if c["should_transition"]]
    assert len(fired) >= 2
    for c in fired:
        assert c["target_state_id"] == "state_0038"  # from the mock state
        assert c["transition"]["duration_ms"] > 0
 
 
def test_no_transition_has_null_fields():
    c = ContractTransitionEngine("s").process_tier3(1000, 0.4, -0.4, 0.9, None)
    VALIDATOR.validate(c)
    assert c["should_transition"] is False
    assert c["target_state_id"] is None and c["transition"] is None
 
 
def test_works_with_null_confidence():
    rows = [(t, 0.5, -0.4, None, "beat") for t in range(1000, 8000, 1000)]
    for c in _run(rows):
        VALIDATOR.validate(c)
 
 
def test_out_of_order_message_is_ignored():
    e = ContractTransitionEngine("s")
    assert e.process_tier3(5000, 0.4, -0.4) is not None
    assert e.process_tier3(4000, 0.4, -0.4) is None
    assert e.process_tier3(5000, 0.4, -0.4) is None
 
 
def test_missing_valence_gives_no_transition():
    c = ContractTransitionEngine("s").process_tier3(1000, None, 0.2)
    VALIDATOR.validate(c)
    assert c["should_transition"] is False
 
 
def test_contract_example_still_valid():
    ex = json.loads((REPO_ROOT / "contracts/examples/transition-command.example.json").read_text(encoding="utf-8"))
    VALIDATOR.validate(ex)
 
 
def test_null_confidence_does_not_apply_confidence_gate():
    # calm -> excited, beat on every frame, confidence null: must still transition
    rows = [(t * 1000, 0.5, -0.5, None, "beat") for t in range(1, 6)]
    rows += [(t * 1000, 0.5, 0.5, None, "beat") for t in range(6, 16)]
    fired = [c for c in _run(rows) if c["should_transition"]]
    assert fired
 
 
def test_real_confidence_below_gate_blocks_transition():
    rows = [(t * 1000, 0.5, -0.5, 0.5, "beat") for t in range(1, 6)]
    rows += [(t * 1000, 0.5, 0.5, 0.5, "beat") for t in range(6, 16)]
    assert not [c for c in _run(rows) if c["should_transition"]]
 