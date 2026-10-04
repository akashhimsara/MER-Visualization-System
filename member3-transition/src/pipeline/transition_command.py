"""
Converts an orchestrator decision into the structured message Member 2
actually needs. This is FR13 from your proposal, word for word:
"transition type, timing, duration, strength, target emotion state, and
confidence."

This module takes the orchestrator's result dict (what process_frame()
already returns) and nothing else - it doesn't re-decide anything, it
only formats the decision that was already made.
"""

# Bigger structural landmarks -> a bigger ("major") visual change.
# Smaller/local landmarks -> a subtler ("minor") one.
MAJOR_LANDMARKS = {"downbeat", "section_boundary"}


def build_transition_command(result):
    """
    result: the dict returned by TransitionOrchestrator.process_frame()

    Returns a dict ready to send to Member 2 (e.g. as the JSON body of a
    WebSocket message). When no transition should happen, still returns a
    valid, minimal message rather than None - Member 2's code shouldn't
    have to special-case "nothing happened" separately from "parse this".
    """
    if not result["transition"]:
        return {
            "type": "transition_command",
            "should_transition": False,
            "timestamp": result["timestamp"],
        }

    candidate_type = result.get("candidate_type")
    transition_type = "major" if candidate_type in MAJOR_LANDMARKS else "minor"

    duration_ms = _choose_duration_ms(
        confidence=result["confidence"],
        persistence=result["persistence"],
    )

    return {
        "type": "transition_command",
        "should_transition": True,
        "transition_type": transition_type,
        "target_emotion": result["emotion"],
        "timing": result["timestamp"],
        "duration_ms": duration_ms,
        "strength": result["score"],
        "confidence": result["confidence"],
    }


def _choose_duration_ms(confidence, persistence):
    """
    Design choice, stated explicitly (put this exact reasoning in your
    report's methodology section - a panel will ask "why these numbers"):
    a confident, persistent emotional state can afford a slower, more
    deliberate transition, since we're sure it's real. A shakier one
    should transition FAST, so it doesn't look hesitant sitting half-way
    between two visual states on screen.
    """
    if confidence >= 0.85 and persistence >= 0.80:
        return 1200
    if confidence >= 0.70:
        return 700
    return 400
