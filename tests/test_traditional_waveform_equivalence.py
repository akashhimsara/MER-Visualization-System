
from pathlib import Path
import sys

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.traditional_features import (
    extract_traditional_features,
)
from src.features.traditional_waveform_features import (
    extract_traditional_waveform_features,
)

AUDIO_PATH = ROOT / "data/raw/deam/MEMD_audio/2.mp3"

SAMPLE_RATE = 22050
CONTEXT_SECONDS = 5.0
TARGET_TIME = 20.0


def main():
    assert AUDIO_PATH.exists(), (
        f"Audio file not found: {AUDIO_PATH}"
    )

    # Original implementation loads the audio itself.
    original = extract_traditional_features(
        AUDIO_PATH,
        TARGET_TIME,
    )

    # New implementation receives the same causal window.
    waveform, sr = librosa.load(
        AUDIO_PATH,
        sr=SAMPLE_RATE,
        mono=True,
        offset=TARGET_TIME - CONTEXT_SECONDS,
        duration=CONTEXT_SECONDS,
    )

    waveform_based = extract_traditional_waveform_features(
        waveform=waveform,
        sample_rate=sr,
    )

    assert original.shape == (86,)
    assert waveform_based.shape == (86,)

    assert np.isfinite(original).all()
    assert np.isfinite(waveform_based).all()

    max_diff = float(
        np.max(np.abs(original - waveform_based))
    )

    np.testing.assert_allclose(
        original,
        waveform_based,
        rtol=1e-6,
        atol=1e-6,
    )

    print("===== TRADITIONAL FEATURE EQUIVALENCE =====")
    print("Audio: TRAIN song 2")
    print("Target time:", TARGET_TIME)
    print("Original shape:", original.shape)
    print("Waveform shape:", waveform_based.shape)
    print(f"Maximum absolute difference: {max_diff:.10f}")
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
