from src.ml.deam_emotion_adapter import (
    map_valence_arousal_to_emotion
)


assert map_valence_arousal_to_emotion(0.5, 0.5) == "Excited"
assert map_valence_arousal_to_emotion(0.5, -0.5) == "Calm"
assert map_valence_arousal_to_emotion(-0.5, 0.5) == "Tense"
assert map_valence_arousal_to_emotion(-0.5, -0.5) == "Sad"

print("DEAM emotion adapter test passed!")