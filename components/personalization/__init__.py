"""
Adaptive Personalization & User Analytics Component.
"""

from components.personalization.presets import (
    PRESET_CALM_NEGATIVE,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_TENSE_NEGATIVE,
    MOCK_COLD_START_PRESETS,
)
from components.personalization.cold_start import select_cold_start_preset
from components.personalization.engine import (
    build_recommendation_event,
    generate_cold_start_recommendation,
)
from components.personalization.feedback import (
    REWARD_DISLIKE,
    REWARD_LIKE,
    REWARD_PRESET_SELECT,
    REWARD_PRESET_SKIP,
    REWARD_VIEW_DURATION,
    RewardResult,
    calculate_reward,
    normalize_rating,
)

__all__ = [
    "PRESET_CALM_NEGATIVE",
    "PRESET_CALM_POSITIVE",
    "PRESET_ENERGETIC_POSITIVE",
    "PRESET_TENSE_NEGATIVE",
    "MOCK_COLD_START_PRESETS",
    "select_cold_start_preset",
    "build_recommendation_event",
    "generate_cold_start_recommendation",
    "REWARD_DISLIKE",
    "REWARD_LIKE",
    "REWARD_PRESET_SELECT",
    "REWARD_PRESET_SKIP",
    "REWARD_VIEW_DURATION",
    "RewardResult",
    "calculate_reward",
    "normalize_rating",
]
