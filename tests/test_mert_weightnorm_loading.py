import torch
from huggingface_hub import hf_hub_download
from transformers import AutoModel

MODEL_NAME = "m-a-p/MERT-v1-95M"

print("===== MERT WEIGHT-NORM LOADING VERIFICATION =====")

# --------------------------------------------------
# Load raw pretrained checkpoint
# --------------------------------------------------

checkpoint_path = hf_hub_download(
    repo_id=MODEL_NAME,
    filename="pytorch_model.bin",
)

checkpoint = torch.load(
    checkpoint_path,
    map_location="cpu",
    weights_only=True,
)

# Some checkpoints may wrap the state dict.
if "state_dict" in checkpoint:
    checkpoint = checkpoint["state_dict"]

g_key = "encoder.pos_conv_embed.conv.weight_g"
v_key = "encoder.pos_conv_embed.conv.weight_v"

assert g_key in checkpoint, f"Missing {g_key}"
assert v_key in checkpoint, f"Missing {v_key}"

checkpoint_g = checkpoint[g_key]
checkpoint_v = checkpoint[v_key]

print("Checkpoint weight_g:", tuple(checkpoint_g.shape))
print("Checkpoint weight_v:", tuple(checkpoint_v.shape))


# --------------------------------------------------
# Load MERT normally
# --------------------------------------------------

model = AutoModel.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
)

conv = model.encoder.pos_conv_embed.conv

loaded_g = (
    conv.parametrizations.weight.original0
    .detach()
    .cpu()
)

loaded_v = (
    conv.parametrizations.weight.original1
    .detach()
    .cpu()
)

print("Loaded original0:", tuple(loaded_g.shape))
print("Loaded original1:", tuple(loaded_v.shape))


# --------------------------------------------------
# Numerical comparison
# --------------------------------------------------

print()

print(
    "weight_g exact equal:",
    torch.equal(checkpoint_g, loaded_g),
)

print(
    "weight_g allclose:",
    torch.allclose(
        checkpoint_g,
        loaded_g,
        rtol=0,
        atol=0,
    ),
)

print(
    "weight_g max abs diff:",
    torch.max(
        torch.abs(checkpoint_g - loaded_g)
    ).item(),
)

print()

print(
    "weight_v exact equal:",
    torch.equal(checkpoint_v, loaded_v),
)

print(
    "weight_v allclose:",
    torch.allclose(
        checkpoint_v,
        loaded_v,
        rtol=0,
        atol=0,
    ),
)

print(
    "weight_v max abs diff:",
    torch.max(
        torch.abs(checkpoint_v - loaded_v)
    ).item(),
)


# --------------------------------------------------
# Decision
# --------------------------------------------------

g_match = torch.equal(
    checkpoint_g,
    loaded_g,
)

v_match = torch.equal(
    checkpoint_v,
    loaded_v,
)

print()
print("===== DECISION =====")

if g_match and v_match:

    print("RESULT: PASS")

    print(
        "Legacy checkpoint weight_g/weight_v "
        "were numerically preserved in the "
        "runtime parametrized model."
    )

    print(
        "The loading warning is therefore "
        "consistent with a naming/reporting "
        "mismatch rather than lost pretrained "
        "WeightNorm parameters."
    )

else:

    print("RESULT: FAIL")

    print(
        "Runtime WeightNorm parameters do NOT "
        "exactly match the pretrained checkpoint."
    )

    print(
        "Do not run full MERT extraction until "
        "the compatibility issue is resolved."
    )