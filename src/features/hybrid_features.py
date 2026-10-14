
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

TRADITIONAL_FILE = (
    ROOT / "data/processed/deam_traditional_features_v1.npz"
)

MERT_CHUNK_DIR = (
    ROOT / "outputs/embeddings/EXP_MERT_001/chunks"
)

EXPECTED_TRAIN = 88153
EXPECTED_VALIDATION = 19965
EXPECTED_TOTAL = EXPECTED_TRAIN + EXPECTED_VALIDATION
EXPECTED_SONGS = 1531

ALLOWED_SPLITS = {"train", "validation"}


def load_hybrid_features(layer):
    """
    Load aligned traditional + MERT features.

    Returns:
        X_train: (88153, 854)
        X_val: (19965, 854)
        yv_train, yv_val
        ya_train, ya_val

    TEST partition is excluded.
    """

    assert layer in (4, 8, 12)

    # Load traditional features.
    with np.load(
        TRADITIONAL_FILE,
        allow_pickle=False,
    ) as data:
        X_traditional = data["X"]

        traditional_meta = pd.DataFrame({
            "song_id": data["song_id"],
            "timestamp_ms": data["timestamp_ms"],
            "split": data["split"],
            "valence": data["valence"],
            "arousal": data["arousal"],
            "traditional_index": np.arange(
                len(data["song_id"])
            ),
        })

    assert X_traditional.shape[1] == 86

    # Exclude TEST before alignment.
    traditional_meta = traditional_meta[
        traditional_meta["split"].isin(
            ALLOWED_SPLITS
        )
    ].copy()

    assert len(traditional_meta) == EXPECTED_TOTAL

    # Load MERT embeddings.
    chunks = sorted(
        MERT_CHUNK_DIR.glob("song_*.npz")
    )

    assert len(chunks) == EXPECTED_SONGS

    mert_features = []
    mert_metadata = []

    offset = 0

    for path in chunks:
        with np.load(
            path,
            allow_pickle=False,
        ) as data:
            embeddings = data[f"layer_{layer}"]

            n = len(data["song_id"])

            assert embeddings.shape == (n, 768)
            assert embeddings.dtype == np.float32
            assert np.isfinite(embeddings).all()

            splits = set(
                data["split"].astype(str)
            )

            assert splits <= ALLOWED_SPLITS
            assert len(splits) == 1

            mert_features.append(embeddings)

            mert_metadata.append(pd.DataFrame({
                "song_id": data["song_id"],
                "timestamp_ms": data["timestamp_ms"],
                "split": data["split"],
                "valence": data["valence"],
                "arousal": data["arousal"],
                "mert_index": np.arange(
                    offset,
                    offset + n,
                ),
            }))

            offset += n

    X_mert = np.concatenate(
        mert_features,
        axis=0,
    ).astype(np.float32)

    mert_meta = pd.concat(
        mert_metadata,
        ignore_index=True,
    )

    assert X_mert.shape == (
        EXPECTED_TOTAL,
        768,
    )

    # Match by song and timestamp, not row order.
    merged = traditional_meta.merge(
        mert_meta,
        on=["song_id", "timestamp_ms"],
        how="inner",
        suffixes=("_traditional", "_mert"),
        validate="one_to_one",
    )

    assert len(merged) == EXPECTED_TOTAL

    assert (
        merged["split_traditional"]
        == merged["split_mert"]
    ).all()

    for target in ("valence", "arousal"):
        assert np.allclose(
            merged[f"{target}_traditional"],
            merged[f"{target}_mert"],
            rtol=0,
            atol=1e-6,
        )

    # Align features using verified row indices.
    traditional_indices = merged[
        "traditional_index"
    ].to_numpy(dtype=np.int64)

    mert_indices = merged[
        "mert_index"
    ].to_numpy(dtype=np.int64)

    X_hybrid = np.concatenate(
        [
            X_traditional[traditional_indices],
            X_mert[mert_indices],
        ],
        axis=1,
    ).astype(np.float32)

    assert X_hybrid.shape == (
        EXPECTED_TOTAL,
        854,
    )

    assert np.isfinite(X_hybrid).all()

    splits = merged[
        "split_traditional"
    ].to_numpy()

    yv = merged[
        "valence_traditional"
    ].to_numpy(dtype=np.float32)

    ya = merged[
        "arousal_traditional"
    ].to_numpy(dtype=np.float32)

    train_mask = splits == "train"
    val_mask = splits == "validation"

    X_train = X_hybrid[train_mask]
    X_val = X_hybrid[val_mask]

    yv_train = yv[train_mask]
    yv_val = yv[val_mask]

    ya_train = ya[train_mask]
    ya_val = ya[val_mask]

    assert X_train.shape == (
        EXPECTED_TRAIN,
        854,
    )

    assert X_val.shape == (
        EXPECTED_VALIDATION,
        854,
    )

    return (
        X_train,
        X_val,
        yv_train,
        yv_val,
        ya_train,
        ya_val,
    )
