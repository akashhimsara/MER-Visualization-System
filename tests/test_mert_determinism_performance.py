from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import librosa
import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.mert_features import extract_mert_layer_embeddings


MODEL_NAME = "m-a-p/MERT-v1-95M"
SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5.0
EXPECTED_SAMPLES = int(SAMPLE_RATE * CONTEXT_SECONDS)
LAYERS = (4, 8, 12)

AUDIO_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "deam"
    / "MEMD_audio"
    / "2.mp3"
)


print("===== MERT DETERMINISM + PERFORMANCE TEST =====")


# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# --------------------------------------------------
# Load one real DEAM causal window
# target = 15 s
# context = [10 s, 15 s]
# --------------------------------------------------

waveform, sr = librosa.load(
    AUDIO_PATH,
    sr=SAMPLE_RATE,
    mono=True,
    offset=10.0,
    duration=CONTEXT_SECONDS,
)

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

print("Audio shape:", waveform.shape)
print("Duration:", waveform.shape[0] / SAMPLE_RATE)


# --------------------------------------------------
# Load MERT
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
# GPU memory reset
# --------------------------------------------------

if device.type == "cuda":
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()


# --------------------------------------------------
# Warm-up
# --------------------------------------------------

print("\nRunning warm-up...")

_ = extract_mert_layer_embeddings(
    waveform=waveform,
    model=model,
    processor=processor,
    device=device,
    sample_rate=SAMPLE_RATE,
    layers=LAYERS,
)

if device.type == "cuda":
    torch.cuda.synchronize()


# --------------------------------------------------
# Run 1
# --------------------------------------------------

if device.type == "cuda":
    torch.cuda.synchronize()

start = time.perf_counter()

embeddings_1 = extract_mert_layer_embeddings(
    waveform=waveform,
    model=model,
    processor=processor,
    device=device,
    sample_rate=SAMPLE_RATE,
    layers=LAYERS,
)

if device.type == "cuda":
    torch.cuda.synchronize()

run1_ms = (time.perf_counter() - start) * 1000.0


# --------------------------------------------------
# Run 2
# --------------------------------------------------

if device.type == "cuda":
    torch.cuda.synchronize()

start = time.perf_counter()

embeddings_2 = extract_mert_layer_embeddings(
    waveform=waveform,
    model=model,
    processor=processor,
    device=device,
    sample_rate=SAMPLE_RATE,
    layers=LAYERS,
)

if device.type == "cuda":
    torch.cuda.synchronize()

run2_ms = (time.perf_counter() - start) * 1000.0


# --------------------------------------------------
# Determinism validation
# --------------------------------------------------

print("\n===== DETERMINISM =====")

for layer in LAYERS:

    emb1 = embeddings_1[layer]
    emb2 = embeddings_2[layer]

    max_abs_diff = float(
        np.max(np.abs(emb1 - emb2))
    )

    exact_equal = np.array_equal(
        emb1,
        emb2,
    )

    allclose = np.allclose(
        emb1,
        emb2,
        rtol=1e-6,
        atol=1e-7,
    )

    print(
        f"Layer {layer}: "
        f"exact_equal={exact_equal}, "
        f"allclose={allclose}, "
        f"max_abs_diff={max_abs_diff:.10f}"
    )

    assert allclose


# --------------------------------------------------
# Performance
# --------------------------------------------------

print("\n===== PERFORMANCE =====")

print(f"Run 1 inference: {run1_ms:.3f} ms")
print(f"Run 2 inference: {run2_ms:.3f} ms")

mean_ms = (run1_ms + run2_ms) / 2.0

print(f"Mean inference: {mean_ms:.3f} ms")


# --------------------------------------------------
# GPU memory
# --------------------------------------------------

if device.type == "cuda":

    allocated_mb = (
        torch.cuda.memory_allocated()
        / (1024 ** 2)
    )

    reserved_mb = (
        torch.cuda.memory_reserved()
        / (1024 ** 2)
    )

    peak_mb = (
        torch.cuda.max_memory_allocated()
        / (1024 ** 2)
    )

    print("\n===== GPU MEMORY =====")

    print(
        f"Current allocated: {allocated_mb:.2f} MB"
    )

    print(
        f"Current reserved: {reserved_mb:.2f} MB"
    )

    print(
        f"Peak allocated: {peak_mb:.2f} MB"
    )


print("\nRESULT: PASS")
print(
    "MERT repeated extraction is numerically "
    "consistent for the same DEAM window."
)
print("TEST partition was not used.")