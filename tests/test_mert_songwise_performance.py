from pathlib import Path
import sys
import time

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

LAYERS = (4, 8, 12)

TARGET_FILE = (
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


print("===== MERT SONG-WISE PERFORMANCE PILOT =====")


# --------------------------------------------------
# Canonical TRAIN/VALIDATION targets
# --------------------------------------------------

targets = pd.read_csv(TARGET_FILE)

targets = targets[
    targets["split"].isin(
        ["train", "validation"]
    )
].copy()

targets = targets.sort_values(
    ["song_id", "timestamp_ms"]
).reset_index(drop=True)

assert not (targets["split"] == "test").any()


# --------------------------------------------------
# Pick one song with enough targets
# --------------------------------------------------

counts = (
    targets.groupby("song_id")
    .size()
    .sort_values(ascending=False)
)

song_id = int(counts.index[0])

song_targets = (
    targets[targets["song_id"] == song_id]
    .sort_values("timestamp_ms")
    .head(20)
    .copy()
)

assert len(song_targets) == 20

print("Selected song:", song_id)
print("Pilot windows:", len(song_targets))
print(
    "Split:",
    song_targets["split"].iloc[0],
)


# --------------------------------------------------
# Device + model
# --------------------------------------------------

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("Device:", device)

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
# Load entire song ONCE
# --------------------------------------------------

audio_path = AUDIO_DIR / f"{song_id}.mp3"

load_start = time.perf_counter()

full_waveform, sr = librosa.load(
    audio_path,
    sr=SAMPLE_RATE,
    mono=True,
)

audio_load_ms = (
    time.perf_counter() - load_start
) * 1000.0

assert sr == SAMPLE_RATE
assert full_waveform.ndim == 1
assert np.isfinite(full_waveform).all()

print(
    f"Full-song samples: {len(full_waveform)}"
)

print(
    f"Full-song duration: "
    f"{len(full_waveform) / SAMPLE_RATE:.3f}s"
)

print(
    f"One-time audio load: "
    f"{audio_load_ms:.3f} ms"
)


# --------------------------------------------------
# Warm-up using first window
# --------------------------------------------------

first_target = float(
    song_targets.iloc[0]["timestamp_sec"]
)

first_start = first_target - CONTEXT_SECONDS

start_sample = int(
    round(first_start * SAMPLE_RATE)
)

end_sample = (
    start_sample + EXPECTED_SAMPLES
)

warmup_waveform = full_waveform[
    start_sample:end_sample
]

assert warmup_waveform.shape == (
    EXPECTED_SAMPLES,
)

_ = extract_mert_layer_embeddings(
    waveform=warmup_waveform,
    model=model,
    processor=processor,
    device=device,
    sample_rate=SAMPLE_RATE,
    layers=LAYERS,
)

if device.type == "cuda":
    torch.cuda.synchronize()


# --------------------------------------------------
# Song-wise extraction
# --------------------------------------------------

window_times_ms = []
results = []

overall_start = time.perf_counter()

for row in song_targets.itertuples(
    index=False
):

    target_sec = float(row.timestamp_sec)

    context_start_sec = (
        target_sec - CONTEXT_SECONDS
    )

    start_sample = int(
        round(
            context_start_sec
            * SAMPLE_RATE
        )
    )

    end_sample = (
        start_sample
        + EXPECTED_SAMPLES
    )

    waveform = full_waveform[
        start_sample:end_sample
    ]

    if waveform.shape[0] < EXPECTED_SAMPLES:

        waveform = np.pad(
            waveform,
            (
                0,
                EXPECTED_SAMPLES
                - waveform.shape[0],
            ),
            mode="constant",
        )

    assert waveform.shape == (
        EXPECTED_SAMPLES,
    )

    if device.type == "cuda":
        torch.cuda.synchronize()

    start = time.perf_counter()

    embeddings = extract_mert_layer_embeddings(
        waveform=waveform,
        model=model,
        processor=processor,
        device=device,
        sample_rate=SAMPLE_RATE,
        layers=LAYERS,
    )

    if device.type == "cuda":
        torch.cuda.synchronize()

    elapsed_ms = (
        time.perf_counter() - start
    ) * 1000.0

    window_times_ms.append(
        elapsed_ms
    )

    for layer in LAYERS:

        embedding = embeddings[layer]

        assert embedding.shape == (768,)
        assert embedding.dtype == np.float32
        assert np.isfinite(
            embedding
        ).all()

    results.append(embeddings)


overall_elapsed = (
    time.perf_counter() - overall_start
)


# --------------------------------------------------
# Summary
# --------------------------------------------------

times = np.asarray(
    window_times_ms,
    dtype=np.float64,
)

print()
print("===== PERFORMANCE =====")

print(
    f"Mean MERT inference: "
    f"{times.mean():.3f} ms"
)

print(
    f"P95 MERT inference: "
    f"{np.percentile(times, 95):.3f} ms"
)

print(
    f"20-window extraction time: "
    f"{overall_elapsed:.3f}s"
)

throughput = (
    len(song_targets)
    / overall_elapsed
)

print(
    f"Extraction throughput: "
    f"{throughput:.2f} windows/sec"
)


# --------------------------------------------------
# Rough full extraction estimate
# --------------------------------------------------

total_windows = len(targets)

estimated_seconds = (
    total_windows / throughput
)

estimated_hours = (
    estimated_seconds / 3600.0
)

print()
print("===== ROUGH FULL-RUN ESTIMATE =====")

print(
    "TRAIN + VALIDATION windows:",
    total_windows,
)

print(
    f"Estimated extraction time: "
    f"{estimated_hours:.2f} hours"
)


print()
print("RESULT: PASS")
print(
    "Full song was loaded once and "
    "20 causal windows were extracted successfully."
)
print("TEST partition was not used.")