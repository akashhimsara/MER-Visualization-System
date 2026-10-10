
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import librosa
import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.features.mert_features import extract_mert_layer_embeddings
from src.models.mert_early_exit import extract_mert_early_exit_embeddings


MODEL_NAME = "m-a-p/MERT-v1-95M"
TARGET_FILE = ROOT / "data/processed/deam_paired_va_targets_v1.csv"
AUDIO_DIR = ROOT / "data/raw/deam/MEMD_audio"

SR = 24000
CONTEXT_SECONDS = 5
EXPECTED_SAMPLES = SR * CONTEXT_SECONDS
LAYERS = (4, 8)


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    targets = pd.read_csv(TARGET_FILE)

    # Explicitly exclude TEST before selecting samples.
    assert {"song_id", "split", "timestamp_sec"}.issubset(
        targets.columns
    )

    allowed = targets[
    targets["split"].isin(["train", "validation"])
].copy()

    assert len(allowed) > 0
    assert not (allowed["split"] == "test").any()

    # Select 5 distinct songs from each allowed partition.
    selected = []

    for split in ("train", "validation"):
        subset = allowed[allowed["split"] == split]

        song_ids = sorted(subset["song_id"].unique())[:5]

        assert len(song_ids) == 5

        for song_id in song_ids:
            song_rows = subset[
                subset["song_id"] == song_id
            ].sort_values("timestamp_ms")

            # Use a middle timestamp to sample real music.
            row = song_rows.iloc[len(song_rows) // 2]

            selected.append(row)

    assert len(selected) == 10

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)

    model.eval()

    print("===== REAL DEAM EARLY EXIT EQUIVALENCE =====")
    print("Device:", device)

    checks = 0

    for row in selected:
        song_id = int(row["song_id"])
        split = str(row["split"])
        timestamp_sec = float(row["timestamp_sec"])

        assert split in ("train", "validation")

        audio_path = AUDIO_DIR / f"{song_id}.mp3"

        waveform_full, sr = librosa.load(
            audio_path,
            sr=SR,
            mono=True,
        )

        assert sr == SR
        assert np.isfinite(waveform_full).all()

        start_sample = int(
            round((timestamp_sec - CONTEXT_SECONDS) * SR)
        )

        end_sample = start_sample + EXPECTED_SAMPLES

        assert start_sample >= 0

        waveform = waveform_full[start_sample:end_sample]

        if len(waveform) < EXPECTED_SAMPLES:
            waveform = np.pad(
                waveform,
                (0, EXPECTED_SAMPLES - len(waveform)),
                mode="constant",
            )

        elif len(waveform) > EXPECTED_SAMPLES:
            waveform = waveform[:EXPECTED_SAMPLES]

        assert waveform.shape == (EXPECTED_SAMPLES,)

        full = extract_mert_layer_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            sample_rate=SR,
            layers=LAYERS,
        )

        early = extract_mert_early_exit_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            sample_rate=SR,
            exit_layer=8,
            requested_layers=LAYERS,
        )

        for layer in LAYERS:
            assert full[layer].shape == (768,)
            assert early[layer].shape == (768,)

            difference = float(
                np.max(np.abs(full[layer] - early[layer]))
            )

            assert np.allclose(
                full[layer],
                early[layer],
                atol=1e-5,
                rtol=1e-5,
            ), (
                f"Mismatch: song={song_id}, "
                f"split={split}, layer={layer}, "
                f"diff={difference}"
            )

            checks += 1

            print(
                f"{split:10s} | "
                f"Song {song_id:4d} | "
                f"Layer {layer} | "
                f"max diff={difference:.8f} | PASS"
            )

    print("Total songs:", len(selected))
    print("Total checks:", checks)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
