from src.ml.label_generator import generate_pseudo_label


def test_positive_label():
    result = {"emotion_changed": True, "confidence": 0.90, "persistence": 0.80, "candidate": True}
    assert generate_pseudo_label(result) == 1


def test_negative_label_no_emotion_change():
    result = {"emotion_changed": False, "confidence": 0.90, "persistence": 0.80, "candidate": True}
    assert generate_pseudo_label(result) == 0


def test_negative_label_low_confidence():
    result = {"emotion_changed": True, "confidence": 0.60, "persistence": 0.80, "candidate": True}
    assert generate_pseudo_label(result) == 0


def test_negative_label_low_persistence():
    result = {"emotion_changed": True, "confidence": 0.90, "persistence": 0.50, "candidate": True}
    assert generate_pseudo_label(result) == 0


def test_negative_label_no_candidate():
    result = {"emotion_changed": True, "confidence": 0.90, "persistence": 0.80, "candidate": False}
    assert generate_pseudo_label(result) == 0
