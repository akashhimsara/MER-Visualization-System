from pathlib import Path
import argparse
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
    / "EXP_MERT_001"
)

CHUNK_DIR = OUTPUT_DIR / "chunks"


def chunk_path(song_id):
    return CHUNK_DIR / f"song_{int(song_id):04d}.npz"


def expected_song_metadata(song_targets):
    song_targets = (
        song_targets
        .sort_values("timestamp_ms")
        .reset_index(drop=True)
    )

    return {
        "song_id": song_targets[
            "song_id"
        ].astype(np.int32).to_numpy(),

        "split": np.asarray(
    song_targets["split"].astype(str).tolist(),
    dtype="U10",
),

        "timestamp_ms": song_targets[
            "timestamp_ms"
        ].astype(np.int64).to_numpy(),

        "timestamp_sec": song_targets[
            "timestamp_sec"
        ].astype(np.float32).to_numpy(),

        "valence": song_targets[
            "valence"
        ].astype(np.float32).to_numpy(),

        "arousal": song_targets[
            "arousal"
        ].astype(np.float32).to_numpy(),
    }


def validate_chunk(path, song_targets):
    """
    Validate an existing per-song chunk against the
    canonical target rows for that exact song.

    Returns:
        (True, message)  -> safe to resume/skip
        (False, message) -> invalid/corrupt chunk
    """

    expected = expected_song_metadata(song_targets)

    try:
        with np.load(
            path,
            allow_pickle=False,
        ) as data:

            required_keys = {
                "song_id",
                "split",
                "timestamp_ms",
                "timestamp_sec",
                "valence",
                "arousal",
                "layer_4",
                "layer_8",
                "layer_12",
            }

            if set(data.files) != required_keys:
                return (
                    False,
                    "unexpected key set",
                )

            n = len(expected["song_id"])

            for key in (
                "song_id",
                "split",
                "timestamp_ms",
                "timestamp_sec",
                "valence",
                "arousal",
            ):
                if len(data[key]) != n:
                    return (
                        False,
                        f"{key} row-count mismatch",
                    )

            for layer in LAYERS:
                arr = data[f"layer_{layer}"]

                if arr.shape != (n, 768):
                    return (
                        False,
                        f"layer_{layer} shape mismatch",
                    )

                if arr.dtype != np.float32:
                    return (
                        False,
                        f"layer_{layer} dtype mismatch",
                    )

                if not np.isfinite(arr).all():
                    return (
                        False,
                        f"layer_{layer} contains "
                        f"non-finite values",
                    )

            if not np.array_equal(
                data["song_id"],
                expected["song_id"],
            ):
                return (
                    False,
                    "song_id mismatch",
                )

            if not np.array_equal(
                data["split"],
                expected["split"],
            ):
                return (
                    False,
                    "split mismatch",
                )

            if not np.array_equal(
                data["timestamp_ms"],
                expected["timestamp_ms"],
            ):
                return (
                    False,
                    "timestamp_ms mismatch",
                )

            if not np.allclose(
                data["timestamp_sec"],
                expected["timestamp_sec"],
                rtol=0.0,
                atol=1e-6,
            ):
                return (
                    False,
                    "timestamp_sec mismatch",
                )

            if not np.allclose(
                data["valence"],
                expected["valence"],
                rtol=0.0,
                atol=1e-6,
            ):
                return (
                    False,
                    "valence mismatch",
                )

            if not np.allclose(
                data["arousal"],
                expected["arousal"],
                rtol=0.0,
                atol=1e-6,
            ):
                return (
                    False,
                    "arousal mismatch",
                )

    except Exception as exc:
        return (
            False,
            f"{type(exc).__name__}: {exc}",
        )

    return True, "valid"


def save_song_chunk(
    song_id,
    song_targets,
    embeddings_by_layer,
):
    """
    Atomically save exactly one completed song.
    """

    CHUNK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_path = chunk_path(song_id)

    temp_path = (
        CHUNK_DIR
        / f"song_{int(song_id):04d}.tmp.npz"
    )

    metadata = expected_song_metadata(
        song_targets
    )

    n = len(metadata["song_id"])

    for layer in LAYERS:
        arr = embeddings_by_layer[layer]

        if arr.shape != (n, 768):
            raise RuntimeError(
                f"Invalid layer {layer} shape "
                f"before save: {arr.shape}"
            )

        if arr.dtype != np.float32:
            raise RuntimeError(
                f"Invalid layer {layer} dtype "
                f"before save: {arr.dtype}"
            )

        if not np.isfinite(arr).all():
            raise RuntimeError(
                f"Non-finite layer {layer} "
                f"embedding before save."
            )

    np.savez_compressed(
        temp_path,

        song_id=metadata["song_id"],
        split=metadata["split"],
        timestamp_ms=metadata[
            "timestamp_ms"
        ],
        timestamp_sec=metadata[
            "timestamp_sec"
        ],
        valence=metadata["valence"],
        arousal=metadata["arousal"],

        layer_4=embeddings_by_layer[4],
        layer_8=embeddings_by_layer[8],
        layer_12=embeddings_by_layer[12],
    )

    # Validate temporary artifact before replacing
    # the final chunk.
    valid, message = validate_chunk(
        temp_path,
        song_targets,
    )

    if not valid:
        if temp_path.exists():
            temp_path.unlink()

        raise RuntimeError(
            f"Temporary chunk validation "
            f"failed for song {song_id}: "
            f"{message}"
        )

    temp_path.replace(final_path)

    # Verify final path too.
    valid, message = validate_chunk(
        final_path,
        song_targets,
    )

    if not valid:
        raise RuntimeError(
            f"Final chunk validation failed "
            f"for song {song_id}: {message}"
        )

    return final_path


def extract_song(
    song_id,
    song_targets,
    model,
    processor,
    device,
):
    audio_path = (
        AUDIO_DIR
        / f"{int(song_id)}.mp3"
    )

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Missing audio: {audio_path}"
        )

    full_waveform, sr = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
    )

    if sr != SAMPLE_RATE:
        raise RuntimeError(
            f"Unexpected sample rate for "
            f"song {song_id}: {sr}"
        )

    if (
        full_waveform.ndim != 1
        or not np.isfinite(
            full_waveform
        ).all()
    ):
        raise RuntimeError(
            f"Invalid waveform for song "
            f"{song_id}"
        )

    song_targets = (
        song_targets
        .sort_values("timestamp_ms")
        .reset_index(drop=True)
    )

    layer_records = {
        layer: []
        for layer in LAYERS
    }

    for row in song_targets.itertuples(
        index=False
    ):
        timestamp_sec = float(
            row.timestamp_sec
        )

        context_start_sec = (
            timestamp_sec
            - CONTEXT_SECONDS
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

        if start_sample < 0:
            raise RuntimeError(
                f"Negative context start "
                f"for song {song_id}"
            )

        waveform = full_waveform[
            start_sample:end_sample
        ]

        if (
            waveform.shape[0]
            < EXPECTED_SAMPLES
        ):
            waveform = np.pad(
                waveform,
                (
                    0,
                    EXPECTED_SAMPLES
                    - waveform.shape[0],
                ),
                mode="constant",
            )

        elif (
            waveform.shape[0]
            > EXPECTED_SAMPLES
        ):
            waveform = waveform[
                :EXPECTED_SAMPLES
            ]

        if waveform.shape != (
            EXPECTED_SAMPLES,
        ):
            raise RuntimeError(
                f"Invalid window shape "
                f"for song {song_id}"
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

        for layer in LAYERS:
            embedding = np.asarray(
                embeddings[layer],
                dtype=np.float32,
            )

            if embedding.shape != (768,):
                raise RuntimeError(
                    f"Invalid layer {layer} "
                    f"embedding shape."
                )

            if not np.isfinite(
                embedding
            ).all():
                raise RuntimeError(
                    f"Non-finite layer {layer} "
                    f"embedding."
                )

            layer_records[layer].append(
                embedding
            )

    embeddings_by_layer = {
        layer: np.stack(
            layer_records[layer]
        ).astype(
            np.float32,
            copy=False,
        )
        for layer in LAYERS
    }

    return embeddings_by_layer


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-songs",
        type=int,
        default=None,
        help=(
            "Optional deterministic number "
            "of canonical TRAIN/VALIDATION "
            "songs for pilot testing."
        ),
    )

    args = parser.parse_args()

    print(
        "===== DEAM MERT CHUNKED "
        "SONG-WISE EXTRACTION ====="
    )

    targets = pd.read_csv(TARGET_FILE)

    targets = targets[
        targets["split"].isin(
            ["train", "validation"]
        )
    ].copy()

    targets = targets.sort_values(
        ["song_id", "timestamp_ms"]
    ).reset_index(drop=True)

    if (
        targets["split"] == "test"
    ).any():
        raise RuntimeError(
            "TEST rows entered extraction set."
        )

    canonical_windows = len(targets)
    canonical_songs = int(
        targets["song_id"].nunique()
    )

    print(
        "Canonical TRAIN + VALIDATION "
        "windows:",
        canonical_windows,
    )

    print(
        "Canonical TRAIN + VALIDATION "
        "songs:",
        canonical_songs,
    )

    selected_song_ids = (
        targets["song_id"]
        .drop_duplicates()
        .astype(int)
        .tolist()
    )

    if args.max_songs is not None:
        if args.max_songs <= 0:
            raise ValueError(
                "--max-songs must be > 0."
            )

        selected_song_ids = (
            selected_song_ids[
                :args.max_songs
            ]
        )

        print(
            "Pilot song limit:",
            len(selected_song_ids),
        )

    selected_targets = targets[
        targets["song_id"].isin(
            selected_song_ids
        )
    ].copy()

    print(
        "Selected windows:",
        len(selected_targets),
    )

    CHUNK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------
    # Resume validation
    # ------------------------------------------

    completed_songs = []
    remaining_songs = []

    for song_id in selected_song_ids:
        song_targets = selected_targets[
            selected_targets[
                "song_id"
            ] == song_id
        ].copy()

        path = chunk_path(song_id)

        if not path.exists():
            remaining_songs.append(song_id)
            continue

        valid, message = validate_chunk(
            path,
            song_targets,
        )

        if not valid:
            raise RuntimeError(
                f"Existing chunk is invalid "
                f"for song {song_id}: "
                f"{message}. "
                f"Delete/fix this chunk before "
                f"continuing."
            )

        completed_songs.append(song_id)

    completed_windows = int(
        selected_targets[
            selected_targets["song_id"].isin(
                completed_songs
            )
        ].shape[0]
    )

    remaining_windows = (
        len(selected_targets)
        - completed_windows
    )

    print(
        "Valid completed songs:",
        len(completed_songs),
    )

    print(
        "Already completed windows:",
        completed_windows,
    )

    print(
        "Remaining songs:",
        len(remaining_songs),
    )

    print(
        "Remaining windows:",
        remaining_windows,
    )

    if not remaining_songs:
        print("Nothing to extract.")
        print("TEST partition used: NO")
        print("RESULT: PASS")
        return

    # ------------------------------------------
    # Device + model
    # ------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)

    processor = (
        Wav2Vec2FeatureExtractor
        .from_pretrained(MODEL_NAME)
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model.to(device)
    model.eval()

    run_start = time.perf_counter()

    newly_extracted_windows = 0

    total_remaining_songs = len(
        remaining_songs
    )

    for song_number, song_id in enumerate(
        remaining_songs,
        start=1,
    ):
        song_targets = selected_targets[
            selected_targets[
                "song_id"
            ] == song_id
        ].copy()

        embeddings_by_layer = extract_song(
            song_id=song_id,
            song_targets=song_targets,
            model=model,
            processor=processor,
            device=device,
        )

        saved_path = save_song_chunk(
            song_id=song_id,
            song_targets=song_targets,
            embeddings_by_layer=(
                embeddings_by_layer
            ),
        )

        newly_extracted_windows += len(
            song_targets
        )

        elapsed = (
            time.perf_counter()
            - run_start
        )

        throughput = (
            newly_extracted_windows
            / elapsed
            if elapsed > 0
            else 0.0
        )

        windows_left = (
            remaining_windows
            - newly_extracted_windows
        )

        eta_seconds = (
            windows_left / throughput
            if throughput > 0
            else 0.0
        )

        print(
            f"[song "
            f"{song_number}/"
            f"{total_remaining_songs}] "
            f"id={song_id} | "
            f"rows={len(song_targets)} | "
            f"saved={saved_path.name} | "
            f"{throughput:.2f} "
            f"windows/sec | "
            f"ETA={eta_seconds / 60.0:.1f} min"
        )

    # ------------------------------------------
    # Final selected-set validation
    # ------------------------------------------

    total_validated_rows = 0

    for song_id in selected_song_ids:
        song_targets = selected_targets[
            selected_targets[
                "song_id"
            ] == song_id
        ].copy()

        path = chunk_path(song_id)

        if not path.exists():
            raise RuntimeError(
                f"Missing final chunk for "
                f"song {song_id}"
            )

        valid, message = validate_chunk(
            path,
            song_targets,
        )

        if not valid:
            raise RuntimeError(
                f"Final validation failed "
                f"for song {song_id}: "
                f"{message}"
            )

        total_validated_rows += len(
            song_targets
        )

    if total_validated_rows != len(
        selected_targets
    ):
        raise RuntimeError(
            "Final validated row count "
            "does not match selected target set."
        )

    elapsed = (
        time.perf_counter()
        - run_start
    )

    print()
    print("===== EXTRACTION SUMMARY =====")

    print(
        "Newly extracted windows:",
        newly_extracted_windows,
    )

    print(
        "Total validated windows:",
        total_validated_rows,
    )

    print(
        "Total validated songs:",
        len(selected_song_ids),
    )

    print(
        f"Run elapsed: {elapsed:.2f}s"
    )

    if (
        elapsed > 0
        and newly_extracted_windows > 0
    ):
        print(
            "New-window throughput: "
            f"{newly_extracted_windows / elapsed:.2f} "
            "windows/sec"
        )

    print("Chunk directory:", CHUNK_DIR)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()