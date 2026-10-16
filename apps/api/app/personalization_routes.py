"""
FastAPI Routes for Adaptive Personalization and User Analytics.

Endpoints:
- POST /api/personalization/recommend
- POST /api/personalization/feedback
- GET /api/personalization/users/{user_id}/state

Identity Boundary:
Accepts caller-supplied user_id for this milestone. JWT-derived identity
will replace caller-supplied user_id in a future authentication milestone.
"""

import json
from pathlib import Path as FilePath
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, field_validator

from components.personalization.presets import MAX_IDENTIFIER_LENGTH
from components.personalization.runtime import PersonalizationRuntimeService

# Modern RFC 9110 status code compatibility
STATUS_UNPROCESSABLE: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

router = APIRouter()

# Schema validators for Contract v1.1
ROOT_DIR = FilePath(__file__).resolve().parents[3]
TIER3_SCHEMA_PATH = ROOT_DIR / "contracts" / "schemas" / "mer-tier3.schema.json"
FEEDBACK_SCHEMA_PATH = ROOT_DIR / "contracts" / "schemas" / "feedback-event.schema.json"

with open(TIER3_SCHEMA_PATH, "r", encoding="utf-8") as f:
    _TIER3_VALIDATOR = Draft202012Validator(json.load(f))

with open(FEEDBACK_SCHEMA_PATH, "r", encoding="utf-8") as f:
    _FEEDBACK_VALIDATOR = Draft202012Validator(json.load(f))


# -----------------------------------------------------------------------------
# Dependency Provider
# -----------------------------------------------------------------------------

_service_instance: Optional[PersonalizationRuntimeService] = None


def get_personalization_service() -> PersonalizationRuntimeService:
    """Dependency provider for PersonalizationRuntimeService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = PersonalizationRuntimeService()
    return _service_instance


def set_personalization_service(service: Optional[PersonalizationRuntimeService]) -> None:
    """Setter to override service in tests or custom runtime configs."""
    global _service_instance
    _service_instance = service


# -----------------------------------------------------------------------------
# Request & Response Models for Swagger UI
# -----------------------------------------------------------------------------


class RecommendRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_IDENTIFIER_LENGTH,
        description=(
            f"Caller-supplied user identifier (1-{MAX_IDENTIFIER_LENGTH} chars). Temporary until JWT authentication is implemented."
        ),
        examples=["user-a"],
    )
    tier3_event: Dict[str, Any] = Field(
        ...,
        description="Contract v1.1 MER Tier 3 event containing continuous valence and arousal.",
        examples=[
            {
                "schema_version": "1.1",
                "event_type": "mer.tier3",
                "session_id": "session-001",
                "sequence": 1,
                "audio_time_ms": 1000,
                "emotion": {
                    "valence": 0.8,
                    "arousal": 0.8,
                    "confidence": None,
                },
            }
        ],
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("user_id cannot be empty or whitespace.")
        if len(clean) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(f"user_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.")
        return clean

    @field_validator("tier3_event")
    @classmethod
    def validate_tier3_session_id(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(v, dict):
            session_id = v.get("session_id")
            if session_id is not None:
                clean_sess = str(session_id).strip()
                if not clean_sess:
                    raise ValueError("session_id cannot be empty or whitespace.")
                if len(clean_sess) > MAX_IDENTIFIER_LENGTH:
                    raise ValueError(f"session_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.")
        return v


class FeedbackRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_IDENTIFIER_LENGTH,
        description=(
            f"Caller-supplied user identifier (1-{MAX_IDENTIFIER_LENGTH} chars). Temporary until JWT authentication is implemented."
        ),
        examples=["user-a"],
    )
    feedback_event: Dict[str, Any] = Field(
        ...,
        description="Contract v1.1 Feedback event containing user interaction and target preset.",
        examples=[
            {
                "schema_version": "1.1",
                "event_type": "feedback.event",
                "session_id": "session-001",
                "sequence": 1,
                "audio_time_ms": 1500,
                "feedback_id": "fb_demo_01",
                "preset_id": "mock-energetic-positive",
                "feedback": {
                    "type": "like",
                },
            }
        ],
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("user_id cannot be empty or whitespace.")
        if len(clean) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(f"user_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.")
        return clean

    @field_validator("feedback_event")
    @classmethod
    def validate_feedback_identifiers(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(v, dict):
            for field_name in ("session_id", "feedback_id", "preset_id"):
                val = v.get(field_name)
                if val is not None:
                    clean_val = str(val).strip()
                    if not clean_val:
                        raise ValueError(f"{field_name} cannot be empty or whitespace.")
                    if len(clean_val) > MAX_IDENTIFIER_LENGTH:
                        raise ValueError(f"{field_name} exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.")
        return v


class FeedbackResponse(BaseModel):
    status: str = Field(
        ...,
        description="Outcome status: 'applied', 'auxiliary', 'duplicate', or 'unmatched'.",
    )
    applied: bool = Field(
        ...,
        description="True if the LinUCB bandit model was updated; False otherwise.",
    )
    feedback_id: Optional[str] = Field(
        None, description="Identifier of the processed feedback event."
    )
    preset_id: Optional[str] = Field(
        None, description="Preset arm associated with the feedback."
    )
    session_id: Optional[str] = Field(None, description="Session identifier.")
    reward: Optional[float] = Field(
        None, description="Scalar numerical reward value if applied."
    )
    arm_updated: Optional[str] = Field(
        None, description="Preset arm updated in LinUCB."
    )
    recommendation_id: Optional[str] = Field(
        None, description="Matched recommendation identifier."
    )
    message: str = Field(..., description="Human-readable outcome description.")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.post(
    "/recommend",
    summary="Generate Adaptive Personalization Recommendation",
    response_description="Contract v1.1 Personalization Recommendation Event",
)
def recommend_preset(
    request: RecommendRequest,
    service: PersonalizationRuntimeService = Depends(get_personalization_service),
) -> Dict[str, Any]:
    """
    Generate the next visual preset recommendation from a MER Tier 3 event.

    - Validates request against Contract v1.1 mer-tier3.schema.json.
    - Resolves/restores user's isolated AdaptivePersonalizationEngine.
    - Emits recommendation via cold-start (initial) or LinUCB (after learning).
    - Preserves Tier 3 session_id, sequence, and audio_time_ms.
    - Persists updated user state and recommendation interaction to PostgreSQL.
    """
    user_id = request.user_id.strip()
    if not user_id:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail="user_id cannot be empty.",
        )
    if len(user_id) > MAX_IDENTIFIER_LENGTH:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=f"user_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.",
        )

    session_id = str(request.tier3_event.get("session_id", "")).strip()
    if not session_id:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail="session_id cannot be empty.",
        )
    if len(session_id) > MAX_IDENTIFIER_LENGTH:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=f"session_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.",
        )

    errors = list(_TIER3_VALIDATOR.iter_errors(request.tier3_event))
    if errors:
        details = "; ".join(e.message for e in errors)
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=f"Invalid MER Tier 3 event according to Contract v1.1: {details}",
        )

    try:
        rec_event = service.recommend(user_id=user_id, tier3_event=request.tier3_event)
        return rec_event
    except ValueError as val_err:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendation: {exc}",
        )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Process User Feedback and Update Bandit Model",
    response_description="Structured outcome of feedback processing and bandit learning",
)
def submit_feedback(
    request: FeedbackRequest,
    service: PersonalizationRuntimeService = Depends(get_personalization_service),
) -> Dict[str, Any]:
    """
    Process a user feedback event to update the LinUCB bandit model and user preferences.

    - Validates request against Contract v1.1 feedback-event.schema.json.
    - Resolves/restores user's isolated AdaptivePersonalizationEngine.
    - Checks duplicate feedback_id across restarts (idempotency).
    - If numerical reward applies (+1 for like, -1 for dislike, rating):
      updates LinUCB, persists bandit matrices and user state to PostgreSQL.
    - If auxiliary feedback (view_duration): records telemetry without updating LinUCB.
    """
    user_id = request.user_id.strip()
    if not user_id:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail="user_id cannot be empty.",
        )
    if len(user_id) > MAX_IDENTIFIER_LENGTH:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=f"user_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.",
        )

    for field_name in ("session_id", "feedback_id", "preset_id"):
        val = request.feedback_event.get(field_name)
        if val is not None:
            clean_val = str(val).strip()
            if not clean_val:
                raise HTTPException(
                    status_code=STATUS_UNPROCESSABLE,
                    detail=f"{field_name} cannot be empty.",
                )
            if len(clean_val) > MAX_IDENTIFIER_LENGTH:
                raise HTTPException(
                    status_code=STATUS_UNPROCESSABLE,
                    detail=f"{field_name} exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.",
                )

    errors = list(_FEEDBACK_VALIDATOR.iter_errors(request.feedback_event))
    if errors:
        details = "; ".join(e.message for e in errors)
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=f"Invalid Feedback event according to Contract v1.1: {details}",
        )

    try:
        result = service.process_feedback(
            user_id=user_id, feedback_event=request.feedback_event
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {exc}",
        )


@router.get(
    "/users/{user_id}/state",
    summary="Retrieve User Personalization State and Analytics",
    response_description="JSON-safe representation of user metrics, preferences, and preset stats",
)
def get_user_personalization_state(
    user_id: str = Path(
        ...,
        min_length=1,
        max_length=MAX_IDENTIFIER_LENGTH,
        description=f"Target user identifier (1-{MAX_IDENTIFIER_LENGTH} chars).",
    ),
    service: PersonalizationRuntimeService = Depends(get_personalization_service),
) -> Dict[str, Any]:
    """
    Retrieve read-only personalization state and interaction history for a user.

    Useful for development inspection, analytics, and the viva progress demonstration.
    """
    clean_user_id = user_id.strip()
    if not clean_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id cannot be empty.",
        )
    if len(clean_user_id) > MAX_IDENTIFIER_LENGTH:
        raise HTTPException(
            status_code=STATUS_UNPROCESSABLE,
            detail=f"user_id exceeds maximum length of {MAX_IDENTIFIER_LENGTH} characters.",
        )

    state = service.get_user_state(clean_user_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User personalization state for '{clean_user_id}' not found.",
        )

    return state
