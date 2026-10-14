"""
Feedback Event and Reward Processing Layer.

Provides deterministic reward calculation for user feedback events conforming
to Contract v1.1 feedback-event.schema.json.
This reward signal will serve as the reward update in future LinUCB contextual bandit models.
"""

from typing import Any, Dict, Optional

# Centralized initial reward policy hyperparameters
REWARD_LIKE: float = 1.0
REWARD_DISLIKE: float = -1.0
REWARD_PRESET_SELECT: float = 0.75
REWARD_PRESET_SKIP: float = -0.75
REWARD_VIEW_DURATION: Optional[float] = None

RATING_NORMALIZATION_OFFSET: float = 3.0
RATING_NORMALIZATION_SCALE: float = 2.0


class RewardResult(dict):
    """
    Structured outcome of reward calculation from a FeedbackEvent.
    Inherits from dict for JSON serialization compatibility and convenient dict key access,
    while also providing typed attribute access.
    """

    def __init__(
        self,
        reward: Optional[float],
        feedback_type: str,
        is_explicit: bool,
        is_auxiliary: bool = False,
        preset_id: Optional[str] = None,
        session_id: Optional[str] = None,
        feedback_id: Optional[str] = None,
        raw_value: Optional[Any] = None,
    ):
        super().__init__(
            reward=reward,
            feedback_type=feedback_type,
            is_explicit=is_explicit,
            is_auxiliary=is_auxiliary,
            preset_id=preset_id,
            session_id=session_id,
            feedback_id=feedback_id,
            raw_value=raw_value,
        )

    @property
    def reward(self) -> Optional[float]:
        return self["reward"]

    @property
    def feedback_type(self) -> str:
        return self["feedback_type"]

    @property
    def is_explicit(self) -> bool:
        return self["is_explicit"]

    @property
    def is_auxiliary(self) -> bool:
        return self["is_auxiliary"]

    @property
    def preset_id(self) -> Optional[str]:
        return self["preset_id"]

    @property
    def session_id(self) -> Optional[str]:
        return self["session_id"]

    @property
    def feedback_id(self) -> Optional[str]:
        return self["feedback_id"]

    @property
    def raw_value(self) -> Optional[Any]:
        return self["raw_value"]


def normalize_rating(rating: int) -> float:
    """
    Normalize an integer rating in 1..5 to the range [-1.0, +1.0] using:
        reward = (rating - 3) / 2

    Rating mapping:
    - 1 -> -1.0
    - 2 -> -0.5
    - 3 ->  0.0
    - 4 -> +0.5
    - 5 -> +1.0
    """
    return (float(rating) - RATING_NORMALIZATION_OFFSET) / RATING_NORMALIZATION_SCALE


def calculate_reward(feedback_event: Dict[str, Any]) -> RewardResult:
    """
    Calculate the scalar reward signal from a valid FeedbackEvent.

    Mapping policy:
    - like          -> +1.0 (explicit)
    - dislike       -> -1.0 (explicit)
    - rating (1..5) -> [-1.0, +1.0] normalized via (rating - 3) / 2 (explicit)
    - preset_select -> +0.75 (implicit/behavioral)
    - preset_skip   -> -0.75 (implicit/behavioral)
    - view_duration -> None (auxiliary/implicit; no direct reward until session context exists)

    Args:
        feedback_event: Dictionary conforming to Contract v1.1 feedback.event schema.

    Returns:
        RewardResult instance containing reward, feedback_type, is_explicit, and metadata.
    """
    feedback = feedback_event.get("feedback", {})
    feedback_type = feedback.get("type")
    preset_id = feedback_event.get("preset_id")
    session_id = feedback_event.get("session_id")
    feedback_id = feedback_event.get("feedback_id")

    if feedback_type == "like":
        reward = REWARD_LIKE
        is_explicit = True
        is_auxiliary = False
        raw_value = None

    elif feedback_type == "dislike":
        reward = REWARD_DISLIKE
        is_explicit = True
        is_auxiliary = False
        raw_value = None

    elif feedback_type == "rating":
        rating = feedback.get("rating")
        if rating is None:
            raise ValueError("Rating feedback event missing required 'rating' field")
        reward = normalize_rating(rating)
        is_explicit = True
        is_auxiliary = False
        raw_value = rating

    elif feedback_type == "preset_select":
        reward = REWARD_PRESET_SELECT
        is_explicit = False
        is_auxiliary = False
        raw_value = None

    elif feedback_type == "preset_skip":
        reward = REWARD_PRESET_SKIP
        is_explicit = False
        is_auxiliary = False
        raw_value = None

    elif feedback_type == "view_duration":
        # Deferred direct reward: raw duration requires session-relative context
        duration_ms = feedback.get("duration_ms")
        reward = REWARD_VIEW_DURATION
        is_explicit = False
        is_auxiliary = True
        raw_value = duration_ms

    else:
        raise ValueError(f"Unknown feedback type: {feedback_type!r}")

    return RewardResult(
        reward=reward,
        feedback_type=feedback_type,
        is_explicit=is_explicit,
        is_auxiliary=is_auxiliary,
        preset_id=preset_id,
        session_id=session_id,
        feedback_id=feedback_id,
        raw_value=raw_value,
    )
