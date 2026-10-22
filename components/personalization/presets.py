"""
Visual Preset ID Registry and Integration Boundary Definitions.

RESPONSIBILITY BOUNDARY:
- Member 2 (Emotion-Aware Visualization Engine) answers:
  "What visuals are suitable for this emotion?"
  Member 2 filters the top-K emotion-safe visual candidates based on Valence/Arousal and audio profile.
- Member 4 (Adaptive Personalization & User Analytics) answers:
  "Among those suitable visuals, which is best for this particular user?"
  Member 4 personalizes strictly within the Member 2 candidate set using LinUCB and user feedback.

DEMO / FALLBACK MODE:
When Member 2 candidate data is NOT supplied, Member 4 falls back to these 4 temporary
mock preset IDs and quadrant mapping for the 50% viva demonstration.
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

# Backward-compatible alias for final integration clarity
DEMO_FALLBACK_VISUALS = MOCK_ARM_PRESETS

# Maximum supported length for bounded database columns and API identifiers
MAX_IDENTIFIER_LENGTH: int = 128
