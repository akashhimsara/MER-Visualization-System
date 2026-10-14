"""
Centralized Visual Preset ID Registry for Personalization Cold-Start.

NOTE:
These preset IDs are temporary mock presets for the initial cold-start milestone.
They must later be replaced with the official visual preset registry owned and
managed by the visualization component (Member 2).
"""

PRESET_ENERGETIC_POSITIVE = "mock-energetic-positive"
PRESET_CALM_POSITIVE = "mock-calm-positive"
PRESET_TENSE_NEGATIVE = "mock-tense-negative"
PRESET_CALM_NEGATIVE = "mock-calm-negative"

MOCK_COLD_START_PRESETS = {
    "energetic_positive": PRESET_ENERGETIC_POSITIVE,
    "calm_positive": PRESET_CALM_POSITIVE,
    "tense_negative": PRESET_TENSE_NEGATIVE,
    "calm_negative": PRESET_CALM_NEGATIVE,
}

MOCK_ARM_PRESETS = list(MOCK_COLD_START_PRESETS.values())
