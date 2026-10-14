
from pathlib import Path

import librosa
import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/traditional_baseline_v1.yaml"


def extract_traditional_waveform_features(
    waveform: np.ndarray,
    sample_rate: int,
) -> np.ndarray:
    """
    Extract the frozen 86D traditional representation
    from an already prepared 5-second causal waveform.

    Input waveform must contain exactly 5 seconds at
    the configured traditional analysis sample rate.
    """

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    expected_sr = int(
        config["audio"]["analysis_sample_rate"]
    )
    context_seconds = float(
        config["temporal"]["context_seconds"]
    )

    n_fft = int(config["stft"]["n_fft"])
    hop_length = int(config["stft"]["hop_length"])
    n_mfcc = int(config["features"]["mfcc"]["n_mfcc"])
    n_chroma = int(config["features"]["chroma"]["n_chroma"])

    if sample_rate != expected_sr:
        raise ValueError(
            f"Expected sample rate {expected_sr}, "
            f"received {sample_rate}"
        )

    y = np.asarray(waveform, dtype=np.float32)

    if y.ndim != 1:
        raise ValueError("Expected mono waveform")

    expected_samples = int(
        round(context_seconds * expected_sr)
    )

    if len(y) != expected_samples:
        raise ValueError(
            f"Expected {expected_samples} samples, "
            f"received {len(y)}"
        )

    if not np.isfinite(y).all():
        raise ValueError("Waveform contains NaN/Inf")

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=expected_sr,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    delta_mfcc = librosa.feature.delta(mfcc)

    chroma = librosa.feature.chroma_stft(
        y=y,
        sr=expected_sr,
        n_fft=n_fft,
        hop_length=hop_length,
        n_chroma=n_chroma,
    )

    rms = librosa.feature.rms(
        y=y,
        frame_length=n_fft,
        hop_length=hop_length,
    )

    centroid = librosa.feature.spectral_centroid(
        y=y,
        sr=expected_sr,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    bandwidth = librosa.feature.spectral_bandwidth(
        y=y,
        sr=expected_sr,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    rolloff = librosa.feature.spectral_rolloff(
        y=y,
        sr=expected_sr,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    zcr = librosa.feature.zero_crossing_rate(
        y,
        frame_length=n_fft,
        hop_length=hop_length,
    )

    frame_features = np.vstack([
        mfcc,
        delta_mfcc,
        chroma,
        rms,
        centroid,
        bandwidth,
        rolloff,
        zcr,
    ])

    if frame_features.shape[0] != 43:
        raise ValueError(
            f"Expected 43 frame dimensions, "
            f"received {frame_features.shape[0]}"
        )

    feature_vector = np.concatenate([
        np.mean(frame_features, axis=1),
        np.std(frame_features, axis=1),
    ]).astype(np.float32)

    if feature_vector.shape != (86,):
        raise ValueError("Expected 86D feature vector")

    if not np.isfinite(feature_vector).all():
        raise ValueError("Non-finite features")

    return feature_vector
