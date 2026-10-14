
from pathlib import Path

import librosa
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

AUDIO_PATH = ROOT / "data/raw/deam/MEMD_audio/2.mp3"

TARGET_TIME = 20.0
CONTEXT_SECONDS = 5.0

TRADITIONAL_SR = 22050
MERT_SR = 24000


def load_window(sample_rate):
    waveform, sr = librosa.load(
        AUDIO_PATH,
        sr=sample_rate,
        mono=True,
        offset=TARGET_TIME - CONTEXT_SECONDS,
        duration=CONTEXT_SECONDS,
    )

    return waveform, sr


def main():
    assert AUDIO_PATH.exists(), "TRAIN audio not found"

    traditional, traditional_sr = load_window(
        TRADITIONAL_SR
    )

    mert, mert_sr = load_window(
        MERT_SR
    )

    assert traditional_sr == TRADITIONAL_SR
    assert mert_sr == MERT_SR

    assert len(traditional) == 110250
    expected_mert_samples = int(
    round(CONTEXT_SECONDS * MERT_SR)
)

    raw_mert_samples = len(mert)

    # Allow at most a one-sample decoding/resampling
    # boundary difference for this diagnostic test.
    assert abs(raw_mert_samples - expected_mert_samples) <= 1, (
      f"Unexpected MERT window length: {raw_mert_samples}"
    )

    # Enforce the frozen 5-second model input length.
    if raw_mert_samples > expected_mert_samples:
      mert = mert[:expected_mert_samples]
    elif raw_mert_samples < expected_mert_samples:
      mert = np.pad(
        mert,
        (0, expected_mert_samples - raw_mert_samples),
        mode="constant",
    )

    assert len(mert) == expected_mert_samples

    print("Raw MERT samples:", raw_mert_samples)
    print("Normalized MERT samples:", len(mert))

    assert traditional.ndim == 1
    assert mert.ndim == 1

    assert np.isfinite(traditional).all()
    assert np.isfinite(mert).all()

    print("===== HYBRID AUDIO WINDOW ALIGNMENT =====")
    print("Audio: TRAIN song 2")
    print("Context: [15.0s, 20.0s]")
    print("Traditional sample rate:", traditional_sr)
    print("Traditional samples:", len(traditional))
    print("MERT sample rate:", mert_sr)
    print("MERT samples:", len(mert))
    print("Both branches requested same audio interval: YES")
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
