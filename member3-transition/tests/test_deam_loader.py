from src.ml.deam_loader import load_deam_annotations


valence_path = (
    "data/deam/annotations/annotations/"
    "annotations averaged per song/"
    "dynamic (per second annotations)/valence.csv"
)

arousal_path = (
    "data/deam/annotations/annotations/"
    "annotations averaged per song/"
    "dynamic (per second annotations)/arousal.csv"
)


annotations = load_deam_annotations(
    valence_path,
    arousal_path
)


assert len(annotations) > 0

first_item = annotations[0]

assert "song_id" in first_item
assert "timestamp_ms" in first_item
assert "valence" in first_item
assert "arousal" in first_item

assert isinstance(first_item["song_id"], int)
assert isinstance(first_item["timestamp_ms"], int)
assert isinstance(first_item["valence"], float)
assert isinstance(first_item["arousal"], float)

print("DEAM loader test passed!")
print("Loaded annotations:", len(annotations))
print("First annotation:", first_item)