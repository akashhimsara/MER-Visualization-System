from pathlib import Path
import hashlib
import time

import librosa
import numpy as np
import pandas as pd
import yaml


CONFIG_PATH = Path("configs/traditional_baseline_v1.yaml")
TARGET_PATH = Path("data/processed/deam_paired_va_targets_v1.csv")
AUDIO_DIR = Path("data/raw/deam/MEMD_audio")

OUTPUT_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_from_window(y, sr, config):

    n_fft = int(config["stft"]["n_fft"])
    hop_length = int(config["stft"]["hop_length"])

    n_mfcc = int(
        config["features"]["mfcc"]["n_mfcc"]
    )

    n_chroma = int(
        config["features"]["chroma"]["n_chroma"]
    )

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    delta_mfcc = librosa.feature.delta(mfcc)

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
            f"Expected 43 frame dimensions, "
            f"got {frame_features.shape[0]}"
        )

    means = np.mean(frame_features, axis=1)
    stds = np.std(frame_features, axis=1)

    vector = np.concatenate(
        [means, stds]
    ).astype(np.float32)

    if vector.shape != (86,):
        raise ValueError(
            f"Expected 86 features, got {vector.shape}"
        )

    if not np.isfinite(vector).all():
        raise ValueError(
            "Feature vector contains NaN/Inf"
        )

    return vector


def sha256_file(path):

    digest = hashlib.sha256()

    with open(path, "rb") as f:

        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def main():

    config = load_config()

    sr = int(
        config["audio"]["analysis_sample_rate"]
    )

    context_seconds = float(
        config["temporal"]["context_seconds"]
    )

    context_samples = int(
        round(context_seconds * sr)
    )

    targets = pd.read_csv(TARGET_PATH)

    targets = targets.sort_values(
        ["song_id", "timestamp_ms"]
    ).reset_index(drop=True)

    total_targets = len(targets)

    X = np.empty(
        (total_targets, 86),
        dtype=np.float32,
    )

    song_ids = targets["song_id"].to_numpy(
        dtype=np.int32
    )

    timestamp_ms = targets[
        "timestamp_ms"
    ].to_numpy(dtype=np.int32)

    valence = targets[
        "valence"
    ].to_numpy(dtype=np.float32)

    arousal = targets[
        "arousal"
    ].to_numpy(dtype=np.float32)

    split = targets[
    "split"
].astype("U10").to_numpy()

    processed = 0
    start_clock = time.perf_counter()

    grouped = targets.groupby(
        "song_id",
        sort=True
    )

    total_songs = grouped.ngroups

    print(
        "===== FULL TRADITIONAL FEATURE EXTRACTION ====="
    )

    print("Songs:", total_songs)
    print("Targets:", total_targets)
    print("Feature dimensions: 86")
    print("Analysis sample rate:", sr)
    print("Context seconds:", context_seconds)

    for song_number, (song_id, group) in enumerate(
        grouped,
        start=1,
    ):

        audio_path = (
            AUDIO_DIR / f"{song_id}.mp3"
        )

        y, loaded_sr = librosa.load(
            audio_path,
            sr=sr,
            mono=True,
        )

        if loaded_sr != sr:
            raise ValueError(
                f"Unexpected sample rate for song {song_id}"
            )

        for row_index, row in group.iterrows():

            target_sec = float(
                row["timestamp_sec"]
            )

            end_sample = int(
                round(target_sec * sr)
            )

            start_sample = (
                end_sample - context_samples
            )

            if start_sample < 0:
                raise ValueError(
                    f"Negative start sample "
                    f"for song {song_id}"
                )

            window = y[
                start_sample:end_sample
            ]

            if len(window) != context_samples:
                raise ValueError(
                    f"Window length mismatch "
                    f"song={song_id}, "
                    f"t={target_sec}"
                )

            X[row_index] = extract_from_window(
                window,
                sr,
                config,
            )

            processed += 1

        if (
            song_number == 1
            or song_number % 100 == 0
            or song_number == total_songs
        ):

            elapsed = (
                time.perf_counter()
                - start_clock
            )

            print(
                f"Song {song_number}/{total_songs} "
                f"| windows {processed}/{total_targets} "
                f"| elapsed {elapsed:.1f}s"
            )

    if not np.isfinite(X).all():
        raise ValueError(
            "Final feature matrix contains NaN/Inf"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savez_compressed(
        OUTPUT_PATH,
        X=X,
        song_id=song_ids,
        timestamp_ms=timestamp_ms,
        valence=valence,
        arousal=arousal,
        split=split,
    )

    elapsed = (
        time.perf_counter()
        - start_clock
    )

    print("\n===== SUMMARY =====")
    print("Feature matrix shape:", X.shape)
    print("Feature dtype:", X.dtype)
    print("Finite:", np.isfinite(X).all())
    print("Processed targets:", processed)
    print("Elapsed seconds:", round(elapsed, 2))
    print("Output:", OUTPUT_PATH)
    print("SHA256:", sha256_file(OUTPUT_PATH))

    if (
        X.shape == (total_targets, 86)
        and processed == total_targets
        and np.isfinite(X).all()
    ):
        print(
            "\nRESULT: PASS - full traditional "
            "feature extraction completed"
        )
    else:
        print("\nRESULT: REVIEW REQUIRED")


if __name__ == "__main__":
    main()