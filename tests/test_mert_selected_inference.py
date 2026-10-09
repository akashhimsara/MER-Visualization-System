
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import torch

from transformers import (
    AutoModel,
    Wav2Vec2FeatureExtractor,
)

from src.features.mert_features import (
    extract_mert_layer_embeddings,
)


MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5
EXPECTED_SAMPLES = SAMPLE_RATE * CONTEXT_SECONDS


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("===== SELECTED MERT INFERENCE SMOKE TEST =====")
    print("Device:", device)

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device)

    model.eval()

    v_scaler = joblib.load(
        MODEL_DIR / "layer_4/scaler.joblib"
    )

    v_model = joblib.load(
        MODEL_DIR / "layer_4/valence_ridge.joblib"
    )

    a_scaler = joblib.load(
        MODEL_DIR / "layer_8/scaler.joblib"
    )

    a_model = joblib.load(
        MODEL_DIR / "layer_8/arousal_ridge.joblib"
    )

    # Synthetic waveform: functional test only.
    # This is NOT an accuracy evaluation.
    t = np.arange(
        EXPECTED_SAMPLES,
        dtype=np.float32,
    ) / SAMPLE_RATE

    waveform = (
        0.1 * np.sin(2 * np.pi * 220.0 * t)
    ).astype(np.float32)

    embeddings = extract_mert_layer_embeddings(
        waveform=waveform,
        model=model,
        processor=processor,
        device=device,
        sample_rate=SAMPLE_RATE,
        layers=(4, 8),
    )

    assert set(embeddings) == {4, 8}
    assert embeddings[4].shape == (768,)
    assert embeddings[8].shape == (768,)

    valence = float(
        v_model.predict(
            v_scaler.transform(
                embeddings[4].reshape(1, -1)
            )
        )[0]
    )

    arousal = float(
        a_model.predict(
            a_scaler.transform(
                embeddings[8].reshape(1, -1)
            )
        )[0]
    )

    assert np.isfinite(valence)
    assert np.isfinite(arousal)

    print("Layer 4 embedding:", embeddings[4].shape)
    print("Layer 8 embedding:", embeddings[8].shape)
    print("Valence prediction:", round(valence, 6))
    print("Arousal prediction:", round(arousal, 6))
    print("Single MERT forward pass: YES")
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
