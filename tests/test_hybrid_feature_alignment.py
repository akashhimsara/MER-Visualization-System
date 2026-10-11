
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

TRADITIONAL_FILE = (
    ROOT / "data/processed/deam_traditional_features_v1.npz"
)

MERT_CHUNK_DIR = (
    ROOT / "outputs/embeddings/EXP_MERT_001/chunks"
)

ALLOWED_SPLITS = {"train", "validation"}


def main():
    print("===== HYBRID FEATURE ALIGNMENT AUDIT =====")

    # Read metadata only from traditional dataset.
    with np.load(TRADITIONAL_FILE, allow_pickle=False) as data:
        traditional = pd.DataFrame({
            "song_id": data["song_id"],
            "timestamp_ms": data["timestamp_ms"],
            "split": data["split"],
            "valence": data["valence"],
            "arousal": data["arousal"],
        })

    traditional = traditional[
        traditional["split"].isin(ALLOWED_SPLITS)
    ].copy()

    assert len(traditional) == 108118
    assert not traditional.duplicated(
        ["song_id", "timestamp_ms"]
    ).any()

    print("Traditional TRAIN/VALIDATION:", len(traditional))

    chunks = sorted(MERT_CHUNK_DIR.glob("*.npz"))
    assert len(chunks) == 1531, (
        f"Unexpected chunk count: {len(chunks)}"
    )

    records = []

    for path in chunks:
        with np.load(path, allow_pickle=False) as data:
            required = {
                "song_id",
                "timestamp_ms",
                "split",
                "valence",
                "arousal",
                "layer_4",
                "layer_8",
            }

            assert required.issubset(data.files), path

            n = len(data["song_id"])

            assert data["layer_4"].shape == (n, 768)
            assert data["layer_8"].shape == (n, 768)

            splits = set(data["split"].tolist())
            assert splits.issubset(ALLOWED_SPLITS), (
                path.name,
                splits,
            )

            assert np.isfinite(data["layer_4"]).all()
            assert np.isfinite(data["layer_8"]).all()

            records.append(pd.DataFrame({
                "song_id": data["song_id"],
                "timestamp_ms": data["timestamp_ms"],
                "split": data["split"],
                "valence": data["valence"],
                "arousal": data["arousal"],
            }))

    mert = pd.concat(records, ignore_index=True)

    assert len(mert) == 108118
    assert not mert.duplicated(
        ["song_id", "timestamp_ms"]
    ).any()

    print("MERT TRAIN/VALIDATION:", len(mert))
    print("MERT chunks:", len(chunks))

    joined = traditional.merge(
        mert,
        on=["song_id", "timestamp_ms"],
        how="outer",
        suffixes=("_traditional", "_mert"),
        indicator=True,
        validate="one_to_one",
    )

    unmatched = joined[
        joined["_merge"] != "both"
    ]

    assert len(unmatched) == 0, (
        f"Unmatched rows: {len(unmatched)}"
    )

    assert (
        joined["split_traditional"]
        == joined["split_mert"]
    ).all()

    for target in ("valence", "arousal"):
        traditional_values = joined[
            f"{target}_traditional"
        ].to_numpy()

        mert_values = joined[
            f"{target}_mert"
        ].to_numpy()

        assert np.allclose(
            traditional_values,
            mert_values,
            rtol=0,
            atol=1e-6,
        ), f"{target} label mismatch"

    print("Matched rows:", len(joined))
    print("Unmatched rows:", len(unmatched))
    print("Duplicate keys: 0")
    print("Split mismatches: 0")
    print("Label mismatches: 0")
    print("TEST embeddings used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
