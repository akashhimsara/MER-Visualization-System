from pathlib import Path

import librosa
import numpy as np
import yaml


CONFIG_PATH = Path("configs/traditional_baseline_v1.yaml")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_traditional_features(
    audio_path: Path,
    target_time_sec: float,
):
    """
    Extract the frozen traditional MER representation
    for one VA target timestamp.

    Context:
        [target_time_sec - 5.0, target_time_sec]

    Returns:
        np.ndarray with shape (86,)
    """

    config = load_config()

    sr = int(
        config["audio"]["analysis_sample_rate"]
    )

    context_seconds = float(
        config["temporal"]["context_seconds"]
    )

    n_fft = int(
        config["stft"]["n_fft"]
    )

    hop_length = int(
        config["stft"]["hop_length"]
    )

    n_mfcc = int(
        config["features"]["mfcc"]["n_mfcc"]
    )

    n_chroma = int(
        config["features"]["chroma"]["n_chroma"]
    )

    start_time = target_time_sec - context_seconds

    if start_time < 0:
        raise ValueError(
            "Context would begin before start of audio"
        )

    # Load only required 5-second context.
    # librosa resamples this traditional branch to 22.05 kHz.
    y, loaded_sr = librosa.load(
        audio_path,
        sr=sr,
        mono=True,
        offset=start_time,
        duration=context_seconds,
    )

    expected_samples = int(
        round(context_seconds * sr)
    )

    if len(y) != expected_samples:
        raise ValueError(
            f"Unexpected window length: "
            f"{len(y)} samples; expected "
            f"{expected_samples}"
        )

    if loaded_sr != sr:
        raise ValueError(
            f"Unexpected sample rate: {loaded_sr}"
        )

    # -----------------------------------------------------
    # Frame-level engineered features
    # -----------------------------------------------------

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    delta_mfcc = librosa.feature.delta(
        mfcc
    )

    chroma = librosa.feature.chroma_stft(
        y=y,
        sr=sr,
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
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    bandwidth = librosa.feature.spectral_bandwidth(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    rolloff = librosa.feature.spectral_rolloff(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    zcr = librosa.feature.zero_crossing_rate(
        y,
        frame_length=n_fft,
        hop_length=hop_length,
    )

    frame_features = np.vstack(
        [
            mfcc,
            delta_mfcc,
            chroma,
            rms,
            centroid,
            bandwidth,
            rolloff,
            zcr,
        ]
    )

    if frame_features.shape[0] != 43:
        raise ValueError(
            f"Expected 43 frame-level dimensions, "
            f"got {frame_features.shape[0]}"
        )

    # -----------------------------------------------------
    # Temporal aggregation
    # -----------------------------------------------------

    feature_mean = np.mean(
        frame_features,
        axis=1
    )

    feature_std = np.std(
        frame_features,
        axis=1
    )

    feature_vector = np.concatenate(
        [
            feature_mean,
            feature_std,
        ]
    ).astype(np.float32)

    if feature_vector.shape != (86,):
        raise ValueError(
            f"Expected 86 features, "
            f"got {feature_vector.shape}"
        )

    if not np.all(np.isfinite(feature_vector)):
        raise ValueError(
            "Feature vector contains NaN or infinity"
        )

    return feature_vector