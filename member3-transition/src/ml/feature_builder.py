def build_features(result):
    return {
        "emotion_changed": int(result["emotion_changed"]),
        "confidence": result.get("confidence", 0.0),
        "persistence": result.get("persistence", 0.0),
        "candidate": int(result["candidate"]),
        "score": result["score"],
        "can_transition": int(result["can_transition"]),
    }