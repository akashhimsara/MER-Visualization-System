from pathlib import Path
import sys
import time
import argparse

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

CHECKPOINT_FILE = (
    OUTPUT_DIR
    / "mert_embeddings_checkpoint.npz"
)


def save_checkpoint(records):

    if not records:
        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = (
        OUTPUT_DIR
        / "mert_embeddings_checkpoint.tmp.npz"
    )

    np.savez_compressed(
        temp_file,

        song_id=np.asarray(
            [r["song_id"] for r in records],
            dtype=np.int32,
        ),

        split=np.asarray(
            [r["split"] for r in records],
            dtype="U10",
        ),

        timestamp_ms=np.asarray(
            [r["timestamp_ms"] for r in records],
            dtype=np.int64,
        ),

        timestamp_sec=np.asarray(
            [r["timestamp_sec"] for r in records],
            dtype=np.float32,
        ),

        valence=np.asarray(
            [r["valence"] for r in records],
            dtype=np.float32,
        ),

        arousal=np.asarray(
            [r["arousal"] for r in records],
            dtype=np.float32,
        ),

        layer_4=np.stack(
            [r["layer_4"] for r in records]
        ).astype(np.float32),

        layer_8=np.stack(
            [r["layer_8"] for r in records]
        ).astype(np.float32),

        layer_12=np.stack(
            [r["layer_12"] for r in records]
        ).astype(np.float32),
    )

    # Replace only after successful write.
    temp_file.replace(CHECKPOINT_FILE)


def load_checkpoint():

    if not CHECKPOINT_FILE.exists():
        return []

    print(
        "Existing checkpoint detected:",
        CHECKPOINT_FILE,
    )

    data = np.load(
        CHECKPOINT_FILE,
        allow_pickle=False,
    )

    n = len(data["song_id"])

    records = []

    for i in range(n):

        records.append(
            {
                "song_id": int(
                    data["song_id"][i]
                ),
                "split": str(
                    data["split"][i]
                ),
                "timestamp_ms": int(
                    data["timestamp_ms"][i]
                ),
                "timestamp_sec": float(
                    data["timestamp_sec"][i]
                ),
                "valence": float(
                    data["valence"][i]
                ),
                "arousal": float(
                    data["arousal"][i]
                ),
                "layer_4": data[
                    "layer_4"
                ][i].astype(
                    np.float32,
                    copy=True,
                ),
                "layer_8": data[
                    "layer_8"
                ][i].astype(
                    np.float32,
                    copy=True,
                ),
                "layer_12": data[
                    "layer_12"
                ][i].astype(
                    np.float32,
                    copy=True,
                ),
            }
        )

    data.close()

    print(
        "Checkpoint rows loaded:",
        len(records),
    )

    return records


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help=(
            "Optional total canonical row limit "
            "for pilot testing."
        ),
    )

    parser.add_argument(
        "--fresh",
        action="store_true",
        help=(
            "Ignore an existing checkpoint and "
            "start extraction from zero."
        ),
    )

    args = parser.parse_args()

    print(
        "===== DEAM MERT SONG-WISE EXTRACTION ====="
    )

    # ----------------------------------------------
    # Canonical TRAIN + VALIDATION rows only
    # ----------------------------------------------

    targets = pd.read_csv(TARGET_FILE)

    targets = targets[
        targets["split"].isin(
            ["train", "validation"]
        )
    ].copy()

    targets = targets.sort_values(
        ["song_id", "timestamp_ms"]
    ).reset_index(drop=True)

    total_train_validation = len(targets)

    print(
        "TRAIN + VALIDATION windows:",
        total_train_validation,
    )

    assert not (
        targets["split"] == "test"
    ).any()

    if args.max_windows is not None:

        targets = targets.head(
            args.max_windows
        ).copy()

        print(
            "Pilot total-row limit:",
            len(targets),
        )

    # ----------------------------------------------
    # Resume state
    # ----------------------------------------------

    if args.fresh:

        records = []

        print(
            "Fresh mode: existing checkpoint "
            "will not be loaded."
        )

    else:

        records = load_checkpoint()

    completed_keys = {
        (
            int(r["song_id"]),
            int(r["timestamp_ms"]),
        )
        for r in records
    }

    if len(completed_keys) != len(records):
        raise RuntimeError(
            "Checkpoint contains duplicate "
            "(song_id, timestamp_ms) keys."
        )

    target_keys = set(
        zip(
            targets["song_id"].astype(int),
            targets["timestamp_ms"].astype(int),
        )
    )

    # Prevent accidentally mixing a checkpoint
    # produced for a different target subset.
    invalid_checkpoint_keys = (
        completed_keys - target_keys
    )

    if invalid_checkpoint_keys:

        raise RuntimeError(
            "Existing checkpoint contains rows "
            "outside the current target set. "
            "Use --fresh for a new pilot/run."
        )

    remaining = targets[
        ~targets.apply(
            lambda row: (
                int(row["song_id"]),
                int(row["timestamp_ms"]),
            )
            in completed_keys,
            axis=1,
        )
    ].copy()

    print(
        "Already completed:",
        len(completed_keys),
    )

    print(
        "Remaining windows:",
        len(remaining),
    )

    if len(remaining) == 0:

        print(
            "Nothing to extract."
        )
        print("RESULT: PASS")
        return

    # ----------------------------------------------
    # Device / model
    # ----------------------------------------------

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

    newly_extracted = 0

    # ----------------------------------------------
    # SONG-WISE extraction
    # ----------------------------------------------

    grouped = remaining.groupby(
        "song_id",
        sort=True,
    )

    total_remaining_songs = (
        remaining["song_id"].nunique()
    )

    for song_number, (
        song_id,
        song_targets,
    ) in enumerate(
        grouped,
        start=1,
    ):

        song_id = int(song_id)

        audio_path = (
            AUDIO_DIR
            / f"{song_id}.mp3"
        )

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Missing audio: {audio_path}"
            )

        # Load/resample the full song exactly once.
        full_waveform, sr = librosa.load(
            audio_path,
            sr=SAMPLE_RATE,
            mono=True,
        )

        if sr != SAMPLE_RATE:
            raise RuntimeError(
                f"Unexpected sample rate "
                f"for song {song_id}: {sr}"
            )

        if (
            full_waveform.ndim != 1
            or not np.isfinite(
                full_waveform
            ).all()
        ):
            raise RuntimeError(
                f"Invalid waveform for "
                f"song {song_id}"
            )

        song_targets = (
            song_targets
            .sort_values("timestamp_ms")
        )

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
                    "Invalid extracted window."
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

            records.append(
                {
                    "song_id": song_id,
                    "split": str(
                        row.split
                    ),
                    "timestamp_ms": int(
                        row.timestamp_ms
                    ),
                    "timestamp_sec":
                        timestamp_sec,
                    "valence": float(
                        row.valence
                    ),
                    "arousal": float(
                        row.arousal
                    ),
                    "layer_4":
                        embeddings[4],
                    "layer_8":
                        embeddings[8],
                    "layer_12":
                        embeddings[12],
                }
            )

            newly_extracted += 1

        # Save after every completed song.
        save_checkpoint(records)

        elapsed = (
            time.perf_counter()
            - run_start
        )

        throughput = (
            newly_extracted / elapsed
            if elapsed > 0
            else 0.0
        )

        print(
            f"[song "
            f"{song_number}/"
            f"{total_remaining_songs}] "
            f"id={song_id} | "
            f"new={newly_extracted} | "
            f"total_saved={len(records)} | "
            f"{throughput:.2f} "
            f"windows/sec"
        )

    # ----------------------------------------------
    # Final validation
    # ----------------------------------------------

    final_keys = {
        (
            int(r["song_id"]),
            int(r["timestamp_ms"]),
        )
        for r in records
    }

    if len(final_keys) != len(records):
        raise RuntimeError(
            "Duplicate keys detected after "
            "extraction."
        )

    expected_keys = set(
        zip(
            targets["song_id"].astype(int),
            targets["timestamp_ms"].astype(int),
        )
    )

    if final_keys != expected_keys:
        raise RuntimeError(
            "Final checkpoint keys do not "
            "match current canonical target set."
        )

    elapsed = (
        time.perf_counter()
        - run_start
    )

    print()
    print("===== EXTRACTION SUMMARY =====")

    print(
        "Newly extracted:",
        newly_extracted,
    )

    print(
        "Total checkpoint rows:",
        len(records),
    )

    print(
        f"Run elapsed: "
        f"{elapsed:.2f} seconds"
    )

    if elapsed > 0:

        print(
            f"New-window throughput: "
            f"{newly_extracted / elapsed:.2f} "
            f"windows/sec"
        )

    print(
        "Checkpoint:",
        CHECKPOINT_FILE,
    )

    print(
        "TEST partition was not used."
    )

    print("RESULT: PASS")


if __name__ == "__main__":
    main()