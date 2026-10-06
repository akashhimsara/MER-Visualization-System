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

CHECKPOINT_FILE = OUTPUT_DIR / "mert_embeddings_checkpoint.npz"


def prepare_waveform(audio_path, start_time):

    waveform, sr = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
        offset=float(start_time),
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

    if sr != SAMPLE_RATE:
        raise RuntimeError(
            f"Unexpected sample rate: {sr}"
        )

    if waveform.shape != (EXPECTED_SAMPLES,):
        raise RuntimeError(
            f"Unexpected waveform shape: {waveform.shape}"
        )

    if not np.isfinite(waveform).all():
        raise RuntimeError(
            "Waveform contains non-finite values."
        )

    return waveform


def save_checkpoint(records):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savez_compressed(
        CHECKPOINT_FILE,

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


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help="Optional limit for pilot testing.",
    )

    args = parser.parse_args()

    print(
        "===== DEAM MERT EMBEDDING EXTRACTION ====="
    )

    # ----------------------------------------------
    # Canonical targets
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

    print(
        "TRAIN + VALIDATION windows:",
        len(targets),
    )

    print(
        "TEST windows used:",
        int((targets["split"] == "test").sum()),
    )

    assert not (
        targets["split"] == "test"
    ).any()

    if args.max_windows is not None:

        targets = targets.head(
            args.max_windows
        ).copy()

        print(
            "Pilot window limit:",
            len(targets),
        )

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

    records = []

    extraction_start = time.perf_counter()

    # ----------------------------------------------
    # Extraction
    # ----------------------------------------------

    for index, row in enumerate(
        targets.itertuples(index=False),
        start=1,
    ):

        song_id = int(row.song_id)
        timestamp_sec = float(row.timestamp_sec)

        start_time = (
            timestamp_sec
            - CONTEXT_SECONDS
        )

        audio_path = (
            AUDIO_DIR
            / f"{song_id}.mp3"
        )

        waveform = prepare_waveform(
            audio_path,
            start_time,
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
                "split": str(row.split),
                "timestamp_ms": int(
                    row.timestamp_ms
                ),
                "timestamp_sec": timestamp_sec,
                "valence": float(row.valence),
                "arousal": float(row.arousal),
                "layer_4": embeddings[4],
                "layer_8": embeddings[8],
                "layer_12": embeddings[12],
            }
        )

        if (
            index % 10 == 0
            or index == len(targets)
        ):

            save_checkpoint(records)

            elapsed = (
                time.perf_counter()
                - extraction_start
            )

            rate = index / elapsed

            print(
                f"[{index}/{len(targets)}] "
                f"saved | "
                f"{rate:.2f} windows/sec"
            )

    elapsed = (
        time.perf_counter()
        - extraction_start
    )

    print()
    print("===== EXTRACTION SUMMARY =====")
    print("Extracted windows:", len(records))
    print(
        f"Elapsed: {elapsed:.2f} seconds"
    )

    if elapsed > 0:
        print(
            f"Average throughput: "
            f"{len(records) / elapsed:.2f} "
            f"windows/sec"
        )

    print(
        "Checkpoint:",
        CHECKPOINT_FILE,
    )

    print("TEST partition was not used.")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()