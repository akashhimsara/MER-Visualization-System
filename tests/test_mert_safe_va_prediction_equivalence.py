
from pathlib import Path
import sys

import joblib
import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.mert_features import (
    extract_mert_layer_embeddings,
)
from src.models.mert_early_exit_safe import (
    extract_mert_early_exit_safe,
)

MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"
SR = 24000
DURATION = 5


def load_predictors():
    predictors = {}

    for target, layer in (
        ("valence", 4),
        ("arousal", 8),
    ):
        folder = MODEL_DIR / f"layer_{layer}"

        predictors[target] = {
            "layer": layer,
            "scaler": joblib.load(
                folder / "scaler.joblib"
            ),
            "ridge": joblib.load(
                folder / f"{target}_ridge.joblib"
            ),
        }

    return predictors


def predict(embeddings, predictors):
    predictions = {}

    for target, components in predictors.items():
        layer = components["layer"]

        X = np.asarray(
            embeddings[layer],
            dtype=np.float32,
        ).reshape(1, -1)

        X_scaled = components["scaler"].transform(X)

        prediction = components["ridge"].predict(
            X_scaled
        )

        predictions[target] = float(prediction[0])

    return predictions


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("===== SAFE MERT VA PREDICTION EQUIVALENCE =====")
    print("Device:", device)

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    ).to(device).eval()

    predictors = load_predictors()

    t = np.arange(
        SR * DURATION,
        dtype=np.float32,
    ) / SR

    rng = np.random.default_rng(42)

    signals = {
        "silence": np.zeros_like(t),
        "220Hz": np.sin(2 * np.pi * 220 * t).astype(np.float32),
        "880Hz": np.sin(2 * np.pi * 880 * t).astype(np.float32),
        "noise": rng.normal(
            0, 0.1, len(t)
        ).astype(np.float32),
    }

    checks = 0

    for name, waveform in signals.items():
        full_embeddings = extract_mert_layer_embeddings(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            sample_rate=SR,
            layers=(4, 8),
        )

        safe_embeddings = extract_mert_early_exit_safe(
            waveform=waveform,
            model=model,
            processor=processor,
            device=device,
            sample_rate=SR,
            exit_layer=8,
            requested_layers=(4, 8),
        )

        full_predictions = predict(
            full_embeddings,
            predictors,
        )

        safe_predictions = predict(
            safe_embeddings,
            predictors,
        )

        for target in ("valence", "arousal"):
            full_value = full_predictions[target]
            safe_value = safe_predictions[target]

            difference = abs(full_value - safe_value)

            passed = np.isclose(
                full_value,
                safe_value,
                rtol=0,
                atol=1e-6,
            )

            print(
                f"{name:8s} | "
                f"{target:7s} | "
                f"full={full_value:.6f} | "
                f"safe={safe_value:.6f} | "
                f"diff={difference:.8f} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

            assert passed, (
                name,
                target,
                full_value,
                safe_value,
            )

            checks += 1

    print("Total prediction checks:", checks)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
