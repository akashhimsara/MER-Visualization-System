import csv


def load_deam_annotations(valence_path, arousal_path):
    valence_rows = {}
    arousal_rows = {}

    with open(valence_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            song_id = row["song_id"]

            for column, value in row.items():
                if column == "song_id":
                    continue

                if value is None or value == "":
                    continue

                valence_rows[(song_id, column)] = float(value)

    with open(arousal_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            song_id = row["song_id"]

            for column, value in row.items():
                if column == "song_id":
                    continue

                if value is None or value == "":
                    continue

                arousal_rows[(song_id, column)] = float(value)

    annotations = []

    for key, valence in valence_rows.items():
        song_id, sample_column = key

        if key not in arousal_rows:
            continue

        timestamp_ms = int(
            sample_column.replace("sample_", "").replace("ms", "")
        )

        annotations.append({
            "song_id": int(song_id),
            "timestamp_ms": timestamp_ms,
            "valence": valence,
            "arousal": arousal_rows[key]
        })

    return annotations