import json
from pathlib import Path

from src.contract.engine_v11 import ContractTransitionEngine, REPO_ROOT

SCHEMA = REPO_ROOT / "contracts" / "schemas" / "transition-command.schema.json"
OUT = Path("demo_output") / "transition_commands_demo.json"


def simulated_stream():
    """(audio_time_ms, valence, arousal, confidence, landmark) every 1 s.
    Calm -> Excited -> Tense, with one noisy flicker in the middle."""
    rows = []
    for s in range(1, 31):
        if s <= 10:
            v, a = 0.45, -0.40          # calm / positive
        elif s <= 20:
            v, a = 0.55, 0.60           # excited
        else:
            v, a = -0.50, 0.55          # tense
        if s == 15:
            v, a = 0.40, -0.30          # one noisy frame
        landmark = "beat" if s % 2 == 0 else ("onset" if s % 3 == 0 else None)
        conf = None if s % 4 == 0 else 0.9    # confidence sometimes null
        rows.append((s * 1000, v, a, conf, landmark))
    return rows


def run():
    engine = ContractTransitionEngine(session_id="sess_demo_001")
    commands = [c for c in (engine.process_tier3(*r) for r in simulated_stream()) if c]

    try:
        import jsonschema
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for c in commands:
            validator.validate(c)
        print(f"Schema validation: PASS ({len(commands)} commands)")
    except ImportError:
        print("jsonschema not installed -> run: pip install jsonschema")

    fired = [c for c in commands if c["should_transition"]]
    for c in fired:
        t = c["transition"]
        print(f"t={c['audio_time_ms']:>6} ms  {c['command_id']}  -> {c['target_state_id']}  "
              f"scale={t['scale']}  duration_ms={t['duration_ms']}  strength={t['strength']}  "
              f"dist={c['reason']['emotion_distance']}  landmark={c['reason']['landmark']}")
    print(f"Transitions: {len(fired)} of {len(commands)} messages")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(fired, indent=2), encoding="utf-8")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    run()
