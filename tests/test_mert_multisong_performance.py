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

N_SONGS = 10
WINDOWS_PER_SONG = 20

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


print("===== MERT MULTI-SONG PERFORMANCE PILOT =====")


# --------------------------------------------------
# Canonical TRAIN + VALIDATION only
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

total_train_validation = len(targets)

print(
    "Canonical TRAIN + VALIDATION windows:",
    total_train_validation,
)


# --------------------------------------------------
# Select deterministic songs
# Need >= WINDOWS_PER_SONG targets
# --------------------------------------------------

counts = (
    targets.groupby("song_id")
    .size()
)

eligible_song_ids = (
    counts[
        counts >= WINDOWS_PER_SONG
    ]
    .index
    .astype(int)
    .sort_values()
)

selected_song_ids = list(
    eligible_song_ids[:N_SONGS]
)

assert len(selected_song_ids) == N_SONGS

print("Selected songs:", selected_song_ids)
print("Windows per song:", WINDOWS_PER_SONG)
print(
    "Total measured windows:",
    N_SONGS * WINDOWS_PER_SONG,
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
# Warm-up
# --------------------------------------------------

warm_song_id = selected_song_ids[0]

warm_row = (
    targets[
        targets["song_id"] == warm_song_id
    ]
    .sort_values("timestamp_ms")
    .iloc[0]
)

warm_audio, sr = librosa.load(
    AUDIO_DIR / f"{warm_song_id}.mp3",
    sr=SAMPLE_RATE,
    mono=True,
)

assert sr == SAMPLE_RATE

warm_end = int(
    round(
        float(warm_row["timestamp_sec"])
        * SAMPLE_RATE
    )
)

warm_start = (
    warm_end - EXPECTED_SAMPLES
)

warm_waveform = warm_audio[
    warm_start:warm_end
]

assert warm_waveform.shape == (
    EXPECTED_SAMPLES,
)

_ = extract_mert_layer_embeddings(
    waveform=warm_waveform,
    model=model,
    processor=processor,
    device=device,
    sample_rate=SAMPLE_RATE,
    layers=LAYERS,
)

if device.type == "cuda":
    torch.cuda.synchronize()


# --------------------------------------------------
# Multi-song benchmark
# --------------------------------------------------

audio_load_times_ms = []
inference_times_ms = []

processed_windows = 0

overall_start = time.perf_counter()

for index, song_id in enumerate(
    selected_song_ids,
    start=1,
):

    song_rows = (
        targets[
            targets["song_id"] == song_id
        ]
        .sort_values("timestamp_ms")
        .head(WINDOWS_PER_SONG)
    )

    assert len(song_rows) == WINDOWS_PER_SONG

    audio_path = (
        AUDIO_DIR / f"{song_id}.mp3"
    )

    load_start = time.perf_counter()

    waveform_full, sr = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
    )

    load_ms = (
        time.perf_counter() - load_start
    ) * 1000.0

    audio_load_times_ms.append(load_ms)

    assert sr == SAMPLE_RATE
    assert waveform_full.ndim == 1
    assert np.isfinite(
        waveform_full
    ).all()

    for row in song_rows.itertuples(
        index=False
    ):

        end_sample = int(
            round(
                float(row.timestamp_sec)
                * SAMPLE_RATE
            )
        )

        start_sample = (
            end_sample - EXPECTED_SAMPLES
        )

        assert start_sample >= 0

        waveform = waveform_full[
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

        inference_start = (
            time.perf_counter()
        )

        embeddings = (
            extract_mert_layer_embeddings(
                waveform=waveform,
                model=model,
                processor=processor,
                device=device,
                sample_rate=SAMPLE_RATE,
                layers=LAYERS,
            )
        )

        if device.type == "cuda":
            torch.cuda.synchronize()

        inference_ms = (
            time.perf_counter()
            - inference_start
        ) * 1000.0

        inference_times_ms.append(
            inference_ms
        )

        for layer in LAYERS:

            embedding = embeddings[layer]

            assert embedding.shape == (768,)
            assert embedding.dtype == np.float32
            assert np.isfinite(
                embedding
            ).all()

        processed_windows += 1

    print(
        f"[{index}/{N_SONGS}] "
        f"song={song_id} | "
        f"audio_load={load_ms:.2f} ms | "
        f"processed={processed_windows}"
    )


if device.type == "cuda":
    torch.cuda.synchronize()

overall_elapsed = (
    time.perf_counter()
    - overall_start
)


# --------------------------------------------------
# Results
# --------------------------------------------------

load_times = np.asarray(
    audio_load_times_ms,
    dtype=np.float64,
)

inference_times = np.asarray(
    inference_times_ms,
    dtype=np.float64,
)

throughput = (
    processed_windows / overall_elapsed
)

estimated_hours = (
    total_train_validation
    / throughput
    / 3600.0
)


print()
print("===== PERFORMANCE SUMMARY =====")

print(
    f"Songs measured: {N_SONGS}"
)

print(
    f"Windows measured: {processed_windows}"
)

print(
    f"Mean full-song load: "
    f"{load_times.mean():.3f} ms"
)

print(
    f"P95 full-song load: "
    f"{np.percentile(load_times, 95):.3f} ms"
)

print(
    f"Total audio loading: "
    f"{load_times.sum() / 1000.0:.3f}s"
)

print(
    f"Mean MERT inference: "
    f"{inference_times.mean():.3f} ms"
)

print(
    f"P95 MERT inference: "
    f"{np.percentile(inference_times, 95):.3f} ms"
)

print(
    f"Overall elapsed: "
    f"{overall_elapsed:.3f}s"
)

print(
    f"End-to-end throughput: "
    f"{throughput:.2f} windows/sec"
)

print()
print("===== ROUGH FULL-RUN ESTIMATE =====")

print(
    "TRAIN + VALIDATION windows:",
    total_train_validation,
)

print(
    f"Estimated full extraction time: "
    f"{estimated_hours:.2f} hours"
)

print()
print("TEST partition used: NO")
print("RESULT: PASS")