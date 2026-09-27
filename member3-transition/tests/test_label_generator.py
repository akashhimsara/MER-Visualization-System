from src.ml.label_generator import generate_pseudo_label


positive_result = {
    "emotion_changed": True,
    "confidence": 0.90,
    "persistence": 0.80,
    "candidate": True,
}

negative_result = {
    "emotion_changed": False,
    "confidence": 0.90,
    "persistence": 0.80,
    "candidate": True,
}

low_confidence_result = {
    "emotion_changed": True,
    "confidence": 0.60,
    "persistence": 0.80,
    "candidate": True,
}

low_persistence_result = {
    "emotion_changed": True,
    "confidence": 0.90,
    "persistence": 0.50,
    "candidate": True,
}

no_candidate_result = {
    "emotion_changed": True,
    "confidence": 0.90,
    "persistence": 0.80,
    "candidate": False,
}


assert generate_pseudo_label(positive_result) == 1
assert generate_pseudo_label(negative_result) == 0
assert generate_pseudo_label(low_confidence_result) == 0
assert generate_pseudo_label(low_persistence_result) == 0
assert generate_pseudo_label(no_candidate_result) == 0

print("Pseudo-label generator test passed!")