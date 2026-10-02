from src.ml.deam_emotion_adapter import map_valence_arousal_to_emotion
from src.ml.deam_loader import load_deam_annotations
from src.pipeline.orchestrator import TransitionOrchestrator


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


def run_deam_sample(song_id=2, number_of_frames=20):
    annotations = load_deam_annotations(
        VALENCE_PATH,
        AROUSAL_PATH
    )

    song_annotations = [
        item
        for item in annotations
        if item["song_id"] == song_id
    ]

    orchestrator = TransitionOrchestrator()

    results = []

    for item in song_annotations[:number_of_frames]:
        emotion = map_valence_arousal_to_emotion(
            item["valence"],
            item["arousal"]
        )

        timestamp = item["timestamp_ms"] / 1000.0

        result = orchestrator.process_frame(
            timestamp=timestamp,
            emotion=emotion,
            confidence=1.0,
            beat=False,
            downbeat=False,
            onset=False,
            energy_change=False
        )

        results.append({
            "song_id": item["song_id"],
            "timestamp_ms": item["timestamp_ms"],
            "valence": item["valence"],
            "arousal": item["arousal"],
            "emotion": emotion,
            "transition": result["transition"],
            "score": result["score"],
            "persistence": result["persistence"]
        })

    return results


if __name__ == "__main__":
    results = run_deam_sample(
        song_id=2,
        number_of_frames=20
    )

    for result in results:
        print(result)