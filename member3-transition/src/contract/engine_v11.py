import json
import math
from pathlib import Path

from src.ml.deam_emotion_adapter import map_valence_arousal_to_emotion
from src.pipeline.orchestrator import TransitionOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_STATE = REPO_ROOT / "contracts" / "examples" / "target-visual-state.example.json"

# PROVISIONAL
MINOR_BELOW = 0.35
MODERATE_BELOW = 0.75
DURATION_MS = {"minor": 400, "moderate": 700, "major": 1200}


class MockTargetStateProvider:
    """Stands in for Member 2's TargetVisualState stream.
    Returns the state_id from the contract example. Replace with the real feed."""

    def __init__(self, path=EXAMPLE_STATE):
        with open(path, encoding="utf-8") as f:
            self.state_id = json.load(f)["state_id"]

    def target_for(self, valence, arousal):
        return self.state_id


def va_margin(valence, arousal):
    """Internal heuristic (NOT a confidence). Used only when MER gives
    confidence = null, so the existing 0.70 gate still has a number."""
    return min(1.0, 0.5 + 1.5 * min(abs(valence), abs(arousal)))


def scale_for(distance):
    if distance < MINOR_BELOW:
        return "minor"
    if distance < MODERATE_BELOW:
        return "moderate"
    return "major"


class ContractTransitionEngine:
    def __init__(self, session_id, state_provider=None, orchestrator=None):
        self.session_id = session_id
        self.provider = state_provider or MockTargetStateProvider()
        self.orchestrator = orchestrator or TransitionOrchestrator()
        self.sequence = 0
        self.last_time_ms = None
        self.anchor_va = None  # VA at start / at last transition

    def _envelope(self, audio_time_ms):
        env = {
            "schema_version": "1.1",
            "event_type": "transition.command",
            "session_id": self.session_id,
            "sequence": self.sequence,
            "audio_time_ms": int(audio_time_ms),
            "command_id": f"trans_{self.sequence:03d}",
        }
        self.sequence += 1
        return env

    def _no_transition(self, audio_time_ms, distance=None, persistence=0.0):
        cmd = self._envelope(audio_time_ms)
        cmd.update(should_transition=False, target_state_id=None, transition=None, reason=None)
        return cmd

    def process_tier3(self, audio_time_ms, valence, arousal, confidence=None, landmark=None):
        """landmark: None | "beat" | "onset" (latest Tier1 event).
        Returns a command dict, or None if the message is stale / out of order."""
        # delayed or duplicate message -> ignore, do not move time backwards
        if self.last_time_ms is not None and audio_time_ms <= self.last_time_ms:
            return None
        self.last_time_ms = audio_time_ms

        # missing values -> no transition, state untouched
        if valence is None or arousal is None:
            return self._no_transition(audio_time_ms)

        if self.anchor_va is None:
            self.anchor_va = (valence, arousal)

        conf = confidence if confidence is not None else va_margin(valence, arousal)
        result = self.orchestrator.process_frame(
            timestamp=audio_time_ms / 1000.0,
            emotion=map_valence_arousal_to_emotion(valence, arousal),
            confidence=conf,
            beat=(landmark == "beat"),
            onset=(landmark == "onset"),
        )
        if not result["transition"]:
            return self._no_transition(audio_time_ms)

        distance = math.dist(self.anchor_va, (valence, arousal))
        scale = scale_for(distance)
        self.anchor_va = (valence, arousal)

        cmd = self._envelope(audio_time_ms)
        cmd.update(
            should_transition=True,
            target_state_id=self.provider.target_for(valence, arousal),
            transition={
                "style": "interpolate",
                "scale": scale,
                "duration_ms": DURATION_MS[scale],
                "strength": round(min(1.0, max(0.0, result["score"])), 2),
            },
            reason={
                "emotion_distance": round(distance, 3),
                "landmark": landmark,
                "persistence": round(min(1.0, max(0.0, result["persistence"])), 2),
            },
        )
        return cmd
