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

__all__ = [
    "PRESET_CALM_NEGATIVE",
    "PRESET_CALM_POSITIVE",
    "PRESET_ENERGETIC_POSITIVE",
    "PRESET_TENSE_NEGATIVE",
    "MOCK_COLD_START_PRESETS",
    "select_cold_start_preset",
    "build_recommendation_event",
    "generate_cold_start_recommendation",
]
