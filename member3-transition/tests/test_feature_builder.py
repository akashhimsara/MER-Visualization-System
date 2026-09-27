from src.ml.feature_builder import build_features


result = {
    "emotion_changed": True,
    "confidence": 0.90,
    "persistence": 0.80,
    "candidate": True,
    "score": 0.75,
    "can_transition": True,
}


features = build_features(result)

assert features["emotion_changed"] == 1
assert features["confidence"] == 0.90
assert features["persistence"] == 0.80
assert features["candidate"] == 1
assert features["score"] == 0.75
assert features["can_transition"] == 1


print("Feature Builder test passed!")