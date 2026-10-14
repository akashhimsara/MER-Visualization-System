"""
Adaptive Personalization & User Analytics Component.
"""

from components.personalization.presets import (
    PRESET_CALM_NEGATIVE,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_TENSE_NEGATIVE,
    MOCK_ARM_PRESETS,
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
from components.personalization.context import (
    CONTEXT_DIMENSION,
    DEFAULT_BIAS_TERM,
    FEATURE_NAMES,
    ContextVector,
    build_context_vector,
)
from components.personalization.linucb import (
    DEFAULT_ALPHA,
    LinUCB,
    LinUCBSelection,
)
from components.personalization.user_state import (
    DEFAULT_MAX_HISTORY_SIZE,
    PresetStats,
    UserPersonalizationState,
)
from components.personalization.adaptive import (
    AdaptivePersonalizationEngine,
    FeedbackProcessingResult,
)

__all__ = [
    # Presets
    "PRESET_ENERGETIC_POSITIVE",
    "PRESET_CALM_POSITIVE",
    "PRESET_TENSE_NEGATIVE",
    "PRESET_CALM_NEGATIVE",
    "MOCK_ARM_PRESETS",
    "MOCK_COLD_START_PRESETS",
    # Cold-Start
    "select_cold_start_preset",
    # Recommendation Builders
    "build_recommendation_event",
    "generate_cold_start_recommendation",
    # Feedback & Rewards
    "calculate_reward",
    "normalize_rating",
    "RewardResult",
    "REWARD_LIKE",
    "REWARD_DISLIKE",
    "REWARD_PRESET_SELECT",
    "REWARD_PRESET_SKIP",
    "REWARD_VIEW_DURATION",
    # Context Vector
    "ContextVector",
    "build_context_vector",
    "DEFAULT_BIAS_TERM",
    "FEATURE_NAMES",
    "CONTEXT_DIMENSION",
    # LinUCB Core
    "LinUCB",
    "LinUCBSelection",
    "DEFAULT_ALPHA",
    # User Personalization State
    "DEFAULT_MAX_HISTORY_SIZE",
    "PresetStats",
    "UserPersonalizationState",
    # Adaptive Learning Engine
    "AdaptivePersonalizationEngine",
    "FeedbackProcessingResult",
]
