from pathlib import Path
import sys

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

AUDIO_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "deam"
    / "MEMD_audio"
    / "2.mp3"
)


print("===== MERT SINGLE-WINDOW FEATURE TEST =====")


# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# --------------------------------------------------
# Load model
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
# Load exactly one real 5-second DEAM window
# --------------------------------------------------

waveform, sr = librosa.load(
    AUDIO_PATH,
    sr=SAMPLE_RATE,
    mono=True,
    offset=15.0,
    duration=CONTEXT_SECONDS,
)

expected_samples = int(
    SAMPLE_RATE * CONTEXT_SECONDS
)

print("Raw loaded audio shape:", waveform.shape)

# Enforce an exact 5.0-second model input.
# librosa/resampling can occasionally return one extra sample.
if waveform.shape[0] < expected_samples:
    waveform = np.pad(
        waveform,
        (0, expected_samples - waveform.shape[0]),
        mode="constant",
    )
elif waveform.shape[0] > expected_samples:
    waveform = waveform[:expected_samples]


print("Final audio shape:", waveform.shape)
print("Sample rate:", sr)
print(
    "Final duration:",
    waveform.shape[0] / sr,
    "seconds",
)


assert sr == SAMPLE_RATE
assert waveform.shape == (expected_samples,)
assert np.isfinite(waveform).all()


# --------------------------------------------------
# MERT extraction
# --------------------------------------------------

embeddings = extract_mert_layer_embeddings(
    waveform=waveform,
    model=model,
    processor=processor,
    device=device,
    sample_rate=SAMPLE_RATE,
    layers=(4, 8, 12),
)


# --------------------------------------------------
# Validate
# --------------------------------------------------

for layer in (4, 8, 12):

    embedding = embeddings[layer]

    print(
        f"Layer {layer}:",
        "shape=",
        embedding.shape,
        "dtype=",
        embedding.dtype,
        "finite=",
        np.isfinite(embedding).all(),
    )

    assert embedding.shape == (768,)
    assert embedding.dtype == np.float32
    assert np.isfinite(embedding).all()


print("\nRESULT: PASS")
print(
    "MERT layers 4/8/12 successfully produced "
    "finite 768D mean-pooled embeddings."
)