"""
Personalization Recommendation Event Builder and Core Service.

Constructs Contract v1.1 personalization.recommendation events from MER Tier 3 inputs.
Separates policy decision logic from event schema construction.
"""

import uuid
from typing import Any, Dict, Optional
from components.personalization.cold_start import select_cold_start_preset
from components.personalization.presets import MAX_IDENTIFIER_LENGTH

# Fixed DNS-derived namespace for deterministic recommendation IDs
RECOMMENDATION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "mer.personalization.recommendation")


def generate_recommendation_id(
    session_id: str,
    sequence: int,
    user_id: Optional[str] = None,
) -> str:
    """
    Generate a deterministic fixed-length recommendation ID using UUID5.
    Guarantees global uniqueness across users and sessions while staying safely
    within bounded database column limits (e.g., VARCHAR(128)).

    Format: rec_<32_hex_chars> (exactly 36 characters total).
    """
    uid_part = str(user_id).strip() if user_id else "anonymous"
    key = f"{uid_part}|{session_id}|{sequence}"
    token = uuid.uuid5(RECOMMENDATION_NAMESPACE, key).hex
    return f"rec_{token}"


def build_recommendation_event(
    session_id: str,
    sequence: int,
    audio_time_ms: int,
    recommended_preset_id: str,
    strategy: str = "cold_start",
    score: Optional[float] = None,
    recommendation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs a dictionary complying with Contract v1.1 recommendation.schema.json.
    Ensures recommendation_id is deterministic, fixed-length (36 chars), and globally unique
    across users sharing session_id, eliminating VARCHAR(128) column overflow risks.
    """
    clean_session_id = str(session_id).strip()
    if len(clean_session_id) > MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"session_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
        )

    clean_preset_id = str(recommended_preset_id).strip()
    if len(clean_preset_id) > MAX_IDENTIFIER_LENGTH:
        raise ValueError(
            f"recommended_preset_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
        )

    if recommendation_id is not None:
        clean_rec_id = str(recommendation_id).strip()
        if len(clean_rec_id) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"recommendation_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
            )
        rec_id = clean_rec_id
    else:
        rec_id = generate_recommendation_id(
            session_id=session_id,
            sequence=sequence,
            user_id=user_id,
        )

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
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a Contract v1.1 recommendation event from a MER Tier 3 event using
    deterministic cold-start quadrant mapping.

    Args:
        tier3_event: Valid MER Tier 3 event dictionary.
        recommendation_sequence: Independent sequence counter for the recommendation stream.
        user_id: Optional user identifier to ensure globally unique recommendation_id across users.

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
        user_id=user_id,
    )
