import csv
import io
import zipfile
from pathlib import Path


AUDIO_ZIP = Path(r"C:\Users\MSI\Downloads\DEAM_audio.zip")
ANNOTATION_ZIP = Path(r"C:\Users\MSI\Downloads\DEAM_Annotations.zip")

AROUSAL_PATH = (
    "annotations/annotations averaged per song/"
    "dynamic (per second annotations)/arousal.csv"
)

VALENCE_PATH = (
    "annotations/annotations averaged per song/"
    "dynamic (per second annotations)/valence.csv"
)


def get_audio_ids():
    with zipfile.ZipFile(AUDIO_ZIP, "r") as z:
        ids = []

        for name in z.namelist():
            if name.lower().endswith(".mp3"):
                ids.append(int(Path(name).stem))

    return ids


def get_annotation_ids(csv_path):
    with zipfile.ZipFile(ANNOTATION_ZIP, "r") as z:
        with z.open(csv_path) as f:
            text = io.TextIOWrapper(f, encoding="utf-8-sig")
            reader = csv.DictReader(text)

            return [int(row["song_id"]) for row in reader]


audio_ids = get_audio_ids()
arousal_ids = get_annotation_ids(AROUSAL_PATH)
valence_ids = get_annotation_ids(VALENCE_PATH)

audio_set = set(audio_ids)
arousal_set = set(arousal_ids)
valence_set = set(valence_ids)

print("===== DEAM ID MAPPING CHECK =====")

print("\nCounts")
print("Audio files:", len(audio_ids))
print("Arousal rows:", len(arousal_ids))
print("Valence rows:", len(valence_ids))

print("\nUnique IDs")
print("Audio:", len(audio_set))
print("Arousal:", len(arousal_set))
print("Valence:", len(valence_set))

print("\nDuplicate IDs")
print("Audio duplicates:", len(audio_ids) - len(audio_set))
print("Arousal duplicates:", len(arousal_ids) - len(arousal_set))
print("Valence duplicates:", len(valence_ids) - len(valence_set))

print("\nMissing relationships")
print("Audio without arousal:", sorted(audio_set - arousal_set))
print("Audio without valence:", sorted(audio_set - valence_set))
print("Arousal without audio:", sorted(arousal_set - audio_set))
print("Valence without audio:", sorted(valence_set - audio_set))

print("\nCross-target consistency")
print("Arousal without valence:", sorted(arousal_set - valence_set))
print("Valence without arousal:", sorted(valence_set - arousal_set))

fully_mapped = audio_set & arousal_set & valence_set

print("\nFully mapped songs:", len(fully_mapped))

if (
    audio_set == arousal_set == valence_set
    and len(audio_ids) == len(audio_set)
    and len(arousal_ids) == len(arousal_set)
    and len(valence_ids) == len(valence_set)
):
    print("\nRESULT: PASS - complete one-to-one song ID mapping")
else:
    print("\nRESULT: REVIEW REQUIRED")