from src.ml.deam_loader import load_deam_annotations

VALENCE_PATH = (
    "data/deam/annotations/annotations/"
    "annotations averaged per song/"
    "dynamic (per second annotations)/valence.csv"
)
AROUSAL_PATH = (
    "data/deam/annotations/annotations/"
    "annotations averaged per song/"
    "dynamic (per second annotations)/arousal.csv"
)


def test_load_deam_annotations():
    annotations = load_deam_annotations(VALENCE_PATH, AROUSAL_PATH)

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
