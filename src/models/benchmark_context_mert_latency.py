from pathlib import Path
import argparse
import gc
import time

import joblib
import librosa
import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor

from src.models.mert_early_exit_safe import extract_mert_early_exit_safe

ROOT = Path(__file__).resolve().parents[2]
MODEL_NAME = "m-a-p/MERT-v1-95M"
SAMPLE_RATE = 24000
WARMUP = 20
RUNS = 100
REPETITIONS = 3
TRAIN_SONG_ID = 2

CONFIGS = {
    3: ("EXP_CONTEXT_3S", 4, 8),
    5: ("EXP_MERT_001", 4, 8),
    8: ("EXP_CONTEXT_8S", 8, 8),
}


def synchronize(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def measure(fn, device):
    for _ in range(WARMUP):
        fn()
    synchronize(device)
    samples = []
    for _ in range(RUNS):
        synchronize(device)
        start = time.perf_counter()
        fn()
        synchronize(device)
        samples.append((time.perf_counter() - start) * 1000.0)
    return np.asarray(samples, dtype=np.float64)


def load_models(context):
    exp_id, valence_layer, arousal_layer = CONFIGS[context]
    root = ROOT / "outputs" / "models" / exp_id
    models = {}
    for target, layer in (("valence", valence_layer), ("arousal", arousal_layer)):
        folder = root / f"layer_{layer}"
        scaler = joblib.load(folder / "scaler.joblib")
        ridge = joblib.load(folder / f"{target}_ridge.joblib")
        if int(getattr(scaler, "n_features_in_", -1)) != 768:
            raise RuntimeError(f"Invalid scaler dimensions: {folder}")
        if int(getattr(ridge, "n_features_in_", -1)) != 768:
            raise RuntimeError(f"Invalid Ridge dimensions: {folder}")
        models[target] = (layer, scaler, ridge)
    return models


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--song-id", type=int, default=TRAIN_SONG_ID)
    args = parser.parse_args()

    split_path = ROOT / "data" / "splits" / "deam_song_split_v1.csv"
    split_df = pd.read_csv(split_path)
    # Require a single explicit TRAIN entry; never benchmark validation or TEST audio.
    if not {"song_id", "split"}.issubset(split_df.columns):
        raise RuntimeError("Unexpected song split CSV columns")
    selected = split_df.loc[split_df["song_id"] == args.song_id, "split"]
    if len(selected) != 1 or str(selected.iloc[0]).lower() != "train":
        raise RuntimeError("Benchmark requires an explicitly TRAIN song")

    audio_path = ROOT / "data" / "raw" / "deam" / "MEMD_audio" / f"{args.song_id}.mp3"
    waveform, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    if sr != SAMPLE_RATE or waveform.ndim != 1 or not np.isfinite(waveform).all():
        raise RuntimeError("Invalid loaded TRAIN audio")

    # Fixed causal endpoint across all contexts, so the audio moment is identical.
    end_sample = 15 * SAMPLE_RATE
    if len(waveform) < end_sample:
        raise RuntimeError("TRAIN audio shorter than fixed 15s endpoint")
    windows = {
        context: np.ascontiguousarray(
            waveform[end_sample - context * SAMPLE_RATE:end_sample],
            dtype=np.float32,
        )
        for context in CONFIGS
    }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True).to(device)
    model.eval()
    selected_models = {context: load_models(context) for context in CONFIGS}

    def make_runner(context):
        v_layer, v_scaler, v_ridge = selected_models[context]["valence"]
        a_layer, a_scaler, a_ridge = selected_models[context]["arousal"]
        window = windows[context]

        def run():
            embeddings = extract_mert_early_exit_safe(
                waveform=window,
                model=model,
                processor=processor,
                device=device,
                sample_rate=SAMPLE_RATE,
                exit_layer=8,
                requested_layers=tuple(sorted({v_layer, a_layer})),
            )
            v = v_ridge.predict(v_scaler.transform(embeddings[v_layer].reshape(1, -1)))[0]
            a = a_ridge.predict(a_scaler.transform(embeddings[a_layer].reshape(1, -1)))[0]
            if not np.isfinite([v, a]).all():
                raise RuntimeError("Non-finite prediction")
            return v, a
        return run

    runners = {context: make_runner(context) for context in CONFIGS}
    orders = [(3, 5, 8), (8, 3, 5), (5, 8, 3)]
    rows = []
    print("===== CONTEXT INFERENCE LATENCY BENCHMARK =====")
    print("TRAIN song:", args.song_id)
    print("Device:", device)
    print("Fixed audio endpoint: 15 seconds")
    print("WARMUP:", WARMUP, "RUNS:", RUNS, "REPETITIONS:", REPETITIONS)
    print("TEST partition used: NO")

    for rep, order in enumerate(orders, start=1):
        for context in order:
            gc.collect()
            times = measure(runners[context], device)
            row = {
                "repetition": rep,
                "context_seconds": context,
                "mean_ms": float(times.mean()),
                "p95_ms": float(np.percentile(times, 95)),
                "min_ms": float(times.min()),
                "max_ms": float(times.max()),
                "runs": RUNS,
                "warmup": WARMUP,
                "device": str(device),
                "song_id": args.song_id,
                "test_used": False,
            }
            rows.append(row)
            print(f"Rep {rep} | {context}s | mean={row['mean_ms']:.3f} ms | P95={row['p95_ms']:.3f} ms")

    df = pd.DataFrame(rows)
    result_path = ROOT / "outputs" / "results" / "EXP_CONTEXT_latency_benchmark.csv"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(result_path, index=False)
    print("\n===== CONTEXT SUMMARY (MEAN OF REPETITIONS) =====")
    print(df.groupby("context_seconds")[["mean_ms", "p95_ms", "max_ms"]].mean().to_string())
    print("Saved:", result_path)
    print("TEST partition used: NO")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
