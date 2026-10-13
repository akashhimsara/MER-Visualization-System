"""
Personalization Recommendation Event Builder and Core Service.

Constructs Contract v1.1 personalization.recommendation events from MER Tier 3 inputs.
Separates policy decision logic from event schema construction.
"""

from typing import Any, Dict, Optional
from components.personalization.cold_start import select_cold_start_preset


def build_recommendation_event(
    session_id: str,
    sequence: int,
    audio_time_ms: int,
    recommended_preset_id: str,
    strategy: str = "cold_start",
    score: Optional[float] = None,
    recommendation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs a dictionary complying with Contract v1.1 recommendation.schema.json.
    """
    rec_id = recommendation_id or f"rec_{session_id}_{sequence}"
    return {
        "schema_version": "1.1",
        "event_type": "personalization.recommendation",
        "session_id": session_id,
        "sequence": sequence,
        "audio_time_ms": audio_time_ms,
        "recommendation_id": rec_id,
        "recommended_preset_id": recommended_preset_id,
        "score": score,
        "strategy": strategy,
    }


def generate_cold_start_recommendation(
    tier3_event: Dict[str, Any],
    recommendation_sequence: int,
) -> Dict[str, Any]:
    """
    Generates a Contract v1.1 recommendation event from a MER Tier 3 event using
    deterministic cold-start quadrant mapping.

    Args:
        tier3_event: Valid MER Tier 3 event dictionary.
        recommendation_sequence: Independent sequence counter for the recommendation stream.

    Returns:
        Dict conforming to contracts/schemas/recommendation.schema.json.
    """
    emotion = tier3_event["emotion"]
    valence = float(emotion["valence"])
    arousal = float(emotion["arousal"])

    preset_id = select_cold_start_preset(valence, arousal)

    return build_recommendation_event(
        session_id=tier3_event["session_id"],
        sequence=recommendation_sequence,
        audio_time_ms=tier3_event["audio_time_ms"],
        recommended_preset_id=preset_id,
        strategy="cold_start",
        score=None,
    )
