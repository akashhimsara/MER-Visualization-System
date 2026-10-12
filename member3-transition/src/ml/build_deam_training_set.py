import csv
import random
from collections import defaultdict
from pathlib import Path

from src.ml.deam_emotion_adapter import map_valence_arousal_to_emotion
from src.ml.deam_loader import load_deam_annotations
from src.pipeline.orchestrator import TransitionOrchestrator
from src.simulator.structure_stream_simulator import generate_structure_frame

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
TRAINING_SET_PATH = Path("data/deam/transition_training_set.csv")

LOOKAHEAD_FRAMES = 6      # 6 frames x 0.5 s = the change must hold for 3 seconds
BEAT_TOLERANCE = 0.25     # DEAM frames are 0.5 s apart -> +/- half a frame
BPM_RANGE = (70, 160)
SEED = 42

# Same order as src/ml/ml_transition_decider.py FEATURE_ORDER - do not reorder.
FEATURE_COLUMNS = [
    "emotion_changed",
    "confidence",
    "persistence",
    "candidate",
    "score",
    "can_transition",
]


def confidence_proxy(valence, arousal):
    """0.5 on a quadrant boundary, rising to 1.0 well inside a quadrant."""
    margin = min(abs(valence), abs(arousal))
    return min(1.0, 0.5 + 1.5 * margin)


def group_by_song(annotations):
    songs = defaultdict(list)
    for item in annotations:
        songs[item["song_id"]].append(item)
    for frames in songs.values():
        frames.sort(key=lambda item: item["timestamp_ms"])
    return songs


def build_rows_for_song(song_id, frames, seed=SEED, lookahead=LOOKAHEAD_FRAMES):
    rng = random.Random(seed + song_id)
    bpm = rng.randint(*BPM_RANGE)

    orchestrator = TransitionOrchestrator()
    # Training-data collection only: we want EVERY smoothed emotion change,
    # not just the confident ones, and no cooldown in the way.
    orchestrator.change_detector.confidence_threshold = 0.0
    orchestrator.continuity_controller.cooldown_seconds = 0.0

    results = []
    for item in frames:
        timestamp = item["timestamp_ms"] / 1000.0
        emotion = map_valence_arousal_to_emotion(item["valence"], item["arousal"])
        structure = generate_structure_frame(
            timestamp, bpm=bpm, beat_tolerance=BEAT_TOLERANCE
        )
        results.append(
            orchestrator.process_frame(
                timestamp=timestamp,
                emotion=emotion,
                confidence=confidence_proxy(item["valence"], item["arousal"]),
                **structure,
            )
        )

    rows = []
    for index, result in enumerate(results):
        if not result["emotion_changed"]:
            continue

        future = results[index + 1:index + 1 + lookahead]
        if len(future) < lookahead:
            continue  # too close to the end of the clip to know the outcome

        sustained = all(f["emotion"] == result["emotion"] for f in future)

        rows.append({
            "song_id": song_id,
            "timestamp_s": result["timestamp"],
            "emotion_changed": int(result["emotion_changed"]),
            "confidence": round(result["confidence"], 4),
            "persistence": result["persistence"],
            "candidate": int(result["candidate"]),
            "score": result["score"],
            "can_transition": int(result["can_transition"]),
            "label": int(sustained),
        })

    return rows


def build_training_set(valence_path=VALENCE_PATH, arousal_path=AROUSAL_PATH):
    annotations = load_deam_annotations(valence_path, arousal_path)
    songs = group_by_song(annotations)

    rows = []
    for song_id in sorted(songs):
        rows.extend(build_rows_for_song(song_id, songs[song_id]))
    return rows


def save_training_set(rows, path=TRAINING_SET_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["song_id", "timestamp_s"] + FEATURE_COLUMNS + ["label"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    rows = build_training_set()
    save_training_set(rows)
    positives = sum(row["label"] for row in rows)
    print("Training set built from REAL DEAM annotations")
    print("Decision rows      :", len(rows))
    print("Songs contributing :", len({row["song_id"] for row in rows}))
    print(f"Sustained (label 1): {positives} ({positives / len(rows):.0%})")
    print("Flicker   (label 0):", len(rows) - positives)
    print("Saved to           :", TRAINING_SET_PATH)