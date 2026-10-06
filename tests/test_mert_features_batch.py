from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import librosa
import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.mert_features import extract_mert_layer_embeddings


MODEL_NAME = "m-a-p/MERT-v1-95M"
SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5.0
EXPECTED_SAMPLES = int(SAMPLE_RATE * CONTEXT_SECONDS)

TARGET_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "deam_paired_va_targets_v1.csv"
)

AUDIO_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "deam"
    / "MEMD_audio"
)

LAYERS = (4, 8, 12)


print("===== MERT SMALL-BATCH FEATURE TEST =====")


# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# --------------------------------------------------
# Load canonical targets
# --------------------------------------------------

targets = pd.read_csv(TARGET_MANIFEST)

# TEST must not be touched for this validation.
targets = targets[
    targets["split"].isin(["train", "validation"])
].copy()

song_ids = sorted(
    targets["song_id"].unique()
)[:3]

print("Selected song IDs:", song_ids)


# --------------------------------------------------
# Select 2 targets from each of 3 songs
# --------------------------------------------------

samples = []

for song_id in song_ids:

    song_targets = (
        targets[targets["song_id"] == song_id]
        .sort_values("timestamp_sec")
        .head(2)
    )

    for row in song_targets.itertuples():

        samples.append(
            {
                "song_id": int(row.song_id),
                "split": row.split,
                "timestamp_sec": float(row.timestamp_sec),
            }
        )


print("Selected windows:", len(samples))

assert len(samples) == 6


# --------------------------------------------------
# Load MERT once
# --------------------------------------------------

processor = Wav2Vec2FeatureExtractor.from_pretrained(
    MODEL_NAME
)

model = AutoModel.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
)

model.to(device)
model.eval()


# --------------------------------------------------
# Extract each window
# --------------------------------------------------

success_count = 0

for i, sample in enumerate(samples, start=1):

    song_id = sample["song_id"]
    split = sample["split"]
    target_time = sample["timestamp_sec"]

    start_time = target_time - CONTEXT_SECONDS

    audio_path = AUDIO_DIR / f"{song_id}.mp3"

    waveform, sr = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
        offset=start_time,
        duration=CONTEXT_SECONDS,
    )

    # Enforce exact 5-second input length.
    if waveform.shape[0] < EXPECTED_SAMPLES:

        waveform = np.pad(
            waveform,
            (0, EXPECTED_SAMPLES - waveform.shape[0]),
            mode="constant",
        )

    elif waveform.shape[0] > EXPECTED_SAMPLES:

        waveform = waveform[:EXPECTED_SAMPLES]

    assert sr == SAMPLE_RATE
    assert waveform.shape == (EXPECTED_SAMPLES,)
    assert np.isfinite(waveform).all()

    embeddings = extract_mert_layer_embeddings(
        waveform=waveform,
        model=model,
        processor=processor,
        device=device,
        sample_rate=SAMPLE_RATE,
        layers=LAYERS,
    )

    for layer in LAYERS:

        embedding = embeddings[layer]

        assert embedding.shape == (768,)
        assert embedding.dtype == np.float32
        assert np.isfinite(embedding).all()

    success_count += 1

    print(
        f"[{i}/6] "
        f"song={song_id} "
        f"split={split} "
        f"target={target_time:.3f}s "
        f"context=[{start_time:.3f}, {target_time:.3f}] "
        f"PASS"
    )


print()
print("Successful windows:", success_count)
print("Failed windows:", len(samples) - success_count)

assert success_count == len(samples)

print()
print("RESULT: PASS")
print(
    "MERT successfully extracted layers 4/8/12 "
    "for multiple canonical DEAM windows."
)
print("TEST partition was not used.")