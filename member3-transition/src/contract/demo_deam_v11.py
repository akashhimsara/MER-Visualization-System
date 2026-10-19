"""
Replay REAL DEAM songs through the Contract v1.1 engine, with and without the
DEAM-trained ML model, and show the transition.command messages that Member 2
would receive.
 
Run:   python -m src.contract.demo_deam_v11            (auto-picks a song)
       python -m src.contract.demo_deam_v11 10        (song id 10)
 
Honest notes (say these in the viva):
  * valence/arousal come from real DEAM annotations (0.5 s steps)
  * confidence is null -> the engine uses its valence/arousal margin heuristic
  * beats are SIMULATED from a random BPM (no DEAM audio features used)
  * the ML model was trained on these same songs -> numbers are EXPLORATORY
"""
import json
import random
import sys
from pathlib import Path
 
import joblib
 
from src.contract.demo_v11 import SCHEMA
from src.contract.engine_v11 import ContractTransitionEngine
from src.ml.build_deam_training_set import (
    AROUSAL_PATH, BEAT_TOLERANCE, BPM_RANGE, LOOKAHEAD_FRAMES, SEED,
    VALENCE_PATH, group_by_song,
)
from src.ml.deam_loader import load_deam_annotations
from src.pipeline.orchestrator import TransitionOrchestrator
from src.simulator.structure_stream_simulator import generate_structure_frame
 
MODEL_PATH = Path("models/transition_model.pkl")
OUT = Path("demo_output") / "deam_transition_commands.json"
 
 
def replay_song(song_id, frames, model=None):
    """Returns [(command, orchestrator_result), ...] for one DEAM song."""
    engine = ContractTransitionEngine(
        f"deam_{song_id}", orchestrator=TransitionOrchestrator(ml_model=model)
    )
    bpm = random.Random(SEED + song_id).randint(*BPM_RANGE)
    out = []
    for f in frames:
        t = f["timestamp_ms"] / 1000.0
        beat = generate_structure_frame(t, bpm=bpm, beat_tolerance=BEAT_TOLERANCE)["beat"]
        cmd = engine.process_tier3(
            f["timestamp_ms"], f["valence"], f["arousal"],
            confidence=None, landmark="beat" if beat else None,
        )
        out.append((cmd, engine.last_result))
    return out
 
 
def count_unnecessary(replayed):
    """A transition is 'unnecessary' (flicker) if the smoothed emotion does not
    stay the same for the next 6 frames (3 s). Same rule as the training label."""
    fired = flicker = unknown = 0
    for i, (cmd, res) in enumerate(replayed):
        if not (cmd and cmd["should_transition"]):
            continue
        fired += 1
        future = replayed[i + 1:i + 1 + LOOKAHEAD_FRAMES]
        if len(future) < LOOKAHEAD_FRAMES:
            unknown += 1
            continue
        if not all(r and r["emotion"] == res["emotion"] for _, r in future):
            flicker += 1
    return fired, flicker, unknown
 
 
def main():
    annotations = load_deam_annotations(VALENCE_PATH, AROUSAL_PATH)
    songs = group_by_song(annotations)
    model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
    if model is None:
        print("No models/transition_model.pkl -> run: python -m src.ml.train_on_deam")
 
    totals = {"rule only": [0, 0, 0], "rule + ML": [0, 0, 0]}
    best = None
    for sid in sorted(songs):
        rule = replay_song(sid, songs[sid], None)
        ml = replay_song(sid, songs[sid], model) if model else None
        for name, rep in (("rule only", rule), ("rule + ML", ml)):
            if rep is None:
                continue
            for k, v in enumerate(count_unnecessary(rep)):
                totals[name][k] += v
        if best is None and ml and any(c and c["should_transition"] for c, _ in ml):
            best = sid
 
    print(f"\nAll {len(songs)} DEAM songs replayed through the Contract v1.1 engine")
    print(f"{'method':<12}{'transitions':>12}{'flicker':>9}{'unnecessary':>13}")
    for name, (fired, flicker, unknown) in totals.items():
        judged = fired - unknown
        rate = f"{flicker / judged:.0%}" if judged else "-"
        print(f"{name:<12}{fired:>12}{flicker:>9}{rate:>13}")
 
    sid = int(sys.argv[1]) if len(sys.argv) > 1 else best
    if sid is None or sid not in songs:
        print("No song to show.")
        return
    shown = replay_song(sid, songs[sid], model)
    cmds = [c for c, _ in shown if c and c["should_transition"]]
    print(f"\nSong {sid}: {len(shown)} frames, {len(cmds)} transition.command sent to Member 2"
          f" ({'rule + ML' if model else 'rule only'})")
    for c in cmds:
        t = c["transition"]
        print(f"  t={c['audio_time_ms']:>6} ms  {c['command_id']}  -> {c['target_state_id']}"
              f"  scale={t['scale']}  duration_ms={t['duration_ms']}  strength={t['strength']}")
    try:
        import jsonschema
        v = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
        for c, _ in shown:
            if c:
                v.validate(c)
        print("Schema validation: PASS (all messages for this song)")
    except ImportError:
        print("jsonschema not installed")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(cmds, indent=2), encoding="utf-8")
    print(f"Saved: {OUT}")
 
 
if __name__ == "__main__":
    main()