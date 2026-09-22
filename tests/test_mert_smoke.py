#MERT model eka mage computer eke hariyata wada karanawada?” kiyala test karana code eka.
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor


MODEL_NAME = "m-a-p/MERT-v1-95M"
SAMPLE_RATE = 24000
DURATION_SECONDS = 5


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Device: {device}")
    print(f"Loading model: {MODEL_NAME}")

    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )

    model = model.to(device)
    model.eval()

    # 5 seconds of silent dummy audio at 24 kHz
    waveform = torch.zeros(SAMPLE_RATE * DURATION_SECONDS)

    inputs = feature_extractor(
        waveform.numpy(),
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt"
    )

    input_values = inputs["input_values"].to(device)

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    with torch.inference_mode():
        outputs = model(
            input_values,
            output_hidden_states=True
        )

    print(f"Input shape: {tuple(input_values.shape)}")
    print(f"Last hidden state shape: {tuple(outputs.last_hidden_state.shape)}")

    if outputs.hidden_states is not None:
        print(f"Number of hidden-state tensors: {len(outputs.hidden_states)}")
        print(f"Final hidden-state shape: {tuple(outputs.hidden_states[-1].shape)}")

    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024 ** 2)
        reserved = torch.cuda.memory_reserved() / (1024 ** 2)
        peak = torch.cuda.max_memory_allocated() / (1024 ** 2)

        print(f"GPU allocated after inference: {allocated:.2f} MB")
        print(f"GPU reserved after inference: {reserved:.2f} MB")
        print(f"Peak GPU memory during inference: {peak:.2f} MB")

    print("MERT smoke test OK")


if __name__ == "__main__":
    main()