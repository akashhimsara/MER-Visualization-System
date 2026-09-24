from pathlib import Path
import librosa

AUDIO_DIR = Path("data/raw/deam/MEMD_audio")

audio_files = sorted(
    AUDIO_DIR.glob("*.mp3"),
    key=lambda p: int(p.stem)
)

print("===== DEAM AUDIO INTEGRITY CHECK =====")
print("MP3 files found:", len(audio_files))

readable = 0
failed = []

sample_rates = {}
durations = []

for i, path in enumerate(audio_files, start=1):
    try:
        # sr=None = keep original sample rate
        # mono=False = do not force mono
        y, sr = librosa.load(
            path,
            sr=None,
            mono=False
        )

        duration = librosa.get_duration(y=y, sr=sr)

        readable += 1
        durations.append(duration)
        sample_rates[sr] = sample_rates.get(sr, 0) + 1

    except Exception as e:
        failed.append((path.name, str(e)))

    if i % 200 == 0:
        print(f"Checked {i}/{len(audio_files)} files...")

print("\n===== RESULTS =====")
print("Total files:", len(audio_files))
print("Readable files:", readable)
print("Failed files:", len(failed))

print("\nSample-rate distribution:")
for sr, count in sorted(sample_rates.items()):
    print(f"  {sr} Hz: {count}")

if durations:
    print("\nDuration statistics:")
    print(f"  Minimum: {min(durations):.3f} s")
    print(f"  Maximum: {max(durations):.3f} s")
    print(f"  Mean: {sum(durations) / len(durations):.3f} s")

if failed:
    print("\nFailed files:")
    for filename, error in failed:
        print(f"  {filename}: {error}")

if len(audio_files) == 1802 and readable == 1802 and not failed:
    print("\nRESULT: PASS - all 1802 DEAM audio files are readable")
else:
    print("\nRESULT: REVIEW REQUIRED")