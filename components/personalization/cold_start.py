"""
Cold-Start Emotion-to-Preset Mapping Policy.

Maps continuous valence and arousal values into visual preset selections
using quadrant-based partitioning.
"""

from components.personalization.presets import (
    PRESET_CALM_NEGATIVE,
    PRESET_CALM_POSITIVE,
    PRESET_ENERGETIC_POSITIVE,
    PRESET_TENSE_NEGATIVE,
)


def select_cold_start_preset(valence: float, arousal: float) -> str:
    """
    Selects a visual preset ID based on valence/arousal quadrant mapping:
    - valence >= 0 and arousal >= 0 -> mock-energetic-positive
    - valence >= 0 and arousal < 0  -> mock-calm-positive
    - valence < 0 and arousal >= 0  -> mock-tense-negative
    - valence < 0 and arousal < 0   -> mock-calm-negative
    """
    if valence >= 0.0:
        if arousal >= 0.0:
            return PRESET_ENERGETIC_POSITIVE
        else:
            return PRESET_CALM_POSITIVE
    else:
        if arousal >= 0.0:
            return PRESET_TENSE_NEGATIVE
        else:
            return PRESET_CALM_NEGATIVE
