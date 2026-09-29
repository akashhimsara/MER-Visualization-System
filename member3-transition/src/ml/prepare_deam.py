import csv
from pathlib import Path

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

OUTPUT_PATH = Path("data/deam/deam_temporal.csv")


def prepare_deam_dataset():
    annotations = load_deam_annotations(
        VALENCE_PATH,
        AROUSAL_PATH
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "song_id",
                "timestamp_ms",
                "valence",
                "arousal"
            ]
        )

        writer.writeheader()

        writer.writerows(annotations)

    return len(annotations)


if __name__ == "__main__":
    count = prepare_deam_dataset()

    print("DEAM temporal dataset created successfully!")
    print("Records:", count)
    print("Saved to:", OUTPUT_PATH)