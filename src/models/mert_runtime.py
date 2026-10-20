
from contextlib import nullcontext
from pathlib import Path

import joblib
import numpy as np
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.models.mert_early_exit_safe import extract_mert_early_exit_safe


ROOT = Path(__file__).resolve().parents[2]

MODEL_NAME = "m-a-p/MERT-v1-95M"
MODEL_DIR = ROOT / "outputs/models/EXP_MERT_001"

SAMPLE_RATE = 24000
CONTEXT_SECONDS = 5.0
CONTEXT_SAMPLES = int(SAMPLE_RATE * CONTEXT_SECONDS)


class MERTRuntime:
    """
    Reusable frozen MERT inference runtime.

    Configuration:
    - 24 kHz mono audio
    - 5-second causal context
    - MERT early-exit at layer 8
    - Layer 4: Valence Ridge
    - Layer 8: Arousal Ridge
    - FP16 mixed precision on CUDA

    This class processes one complete audio window.
    Rolling buffering and streaming are handled separately.
    """

    def __init__(self, precision="fp16", device=None):
        if precision not in ("fp32", "fp16"):
            raise ValueError(
                "precision must be 'fp32' or 'fp16'"
            )

        if device is None:
            device = (
                "cuda" if torch.cuda.is_available() else "cpu"
            )

        self.device = torch.device(device)
        self.precision = precision

        if self.precision == "fp16" and self.device.type != "cuda":
            raise RuntimeError(
                "FP16 mixed precision requires CUDA"
            )

        self.processor = (
            Wav2Vec2FeatureExtractor.from_pretrained(
                MODEL_NAME,
                trust_remote_code=True,
            )
        )

        self.model = AutoModel.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
        ).to(self.device)

        self.model.eval()

        self.valence_scaler = joblib.load(
            MODEL_DIR / "layer_4/scaler.joblib"
        )
        self.valence_model = joblib.load(
            MODEL_DIR / "layer_4/valence_ridge.joblib"
        )

        self.arousal_scaler = joblib.load(
            MODEL_DIR / "layer_8/scaler.joblib"
        )
        self.arousal_model = joblib.load(
            MODEL_DIR / "layer_8/arousal_ridge.joblib"
        )

    def predict(self, window):
        """
        Predict Valence and Arousal for one 5-second window.

        Input:
            window: 1D mono waveform at 24 kHz.

        Output:
            dict with valence and arousal.
        """

        waveform = np.asarray(window, dtype=np.float32)

        if waveform.ndim != 1:
            raise ValueError(
                "Expected a 1D mono audio waveform"
            )

        if len(waveform) != CONTEXT_SAMPLES:
            raise ValueError(
                f"Expected {CONTEXT_SAMPLES} samples, "
                f"received {len(waveform)}"
            )

        if not np.isfinite(waveform).all():
            raise ValueError(
                "Waveform contains non-finite values"
            )

        if self.precision == "fp16":
            context = torch.autocast(
                device_type="cuda",
                dtype=torch.float16,
            )
        else:
            context = nullcontext()

        with context:
            embeddings = extract_mert_early_exit_safe(
                waveform=waveform,
                model=self.model,
                processor=self.processor,
                device=self.device,
                sample_rate=SAMPLE_RATE,
                exit_layer=8,
                requested_layers=(4, 8),
            )

        valence = float(
            self.valence_model.predict(
                self.valence_scaler.transform(
                    embeddings[4].reshape(1, -1)
                )
            )[0]
        )

        arousal = float(
            self.arousal_model.predict(
                self.arousal_scaler.transform(
                    embeddings[8].reshape(1, -1)
                )
            )[0]
        )

        if not np.isfinite([valence, arousal]).all():
            raise ValueError(
                "Non-finite MER prediction"
            )

        return {
            "valence": valence,
            "arousal": arousal,
        }
