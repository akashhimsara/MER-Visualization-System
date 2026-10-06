from pathlib import Path
import yaml


CONFIG_PATH = Path(
    "configs/mert_baseline_v1.yaml"
)

print("===== MERT BASELINE CONFIG CHECK =====")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


# --------------------------------------------------
# Model
# --------------------------------------------------

assert config["model_name"] == "m-a-p/MERT-v1-95M"

assert (
    config["representation"]["model_mode"]
    == "frozen"
)

assert (
    config["representation"]["hidden_size"]
    == 768
)


# --------------------------------------------------
# Audio / context
# --------------------------------------------------

assert config["audio"]["context_seconds"] == 5.0

assert config["audio"]["context_type"] == "causal"

assert config["audio"]["sample_rate"] == 24000

assert config["audio"]["mono"] is True


# --------------------------------------------------
# Representation candidates
# --------------------------------------------------

layers = config["representation"]["candidate_layers"]

assert layers == [4, 8, 12]

assert config["representation"]["aggregation"] == ["mean"]

assert (
    config["representation"]["layer_selection_split"]
    == "validation"
)


# --------------------------------------------------
# Regression
# --------------------------------------------------

assert config["regression"]["model"] == "ridge"

assert (
    config["regression"]["separate_target_models"]
    is True
)

assert config["regression"]["alpha_candidates"] == [
    0.01,
    0.1,
    1.0,
    10.0,
    100.0,
]

assert (
    config["regression"]["selection_split"]
    == "validation"
)


# --------------------------------------------------
# TEST lock
# --------------------------------------------------

assert config["dataset"]["test_locked"] is True

assert (
    config["test_policy"]["evaluate_test"]
    is False
)

assert (
    config["dataset"]["target_manifest"]
    == "data/processed/deam_paired_va_targets_v1.csv"
)
print("Canonical target manifest: PASS")


# --------------------------------------------------
# Metrics
# --------------------------------------------------

assert config["evaluation"]["metrics"] == [
    "mae",
    "rmse",
    "pearson",
    "ccc",
    "r2",
]


print("Model: PASS")
print("Frozen representation: PASS")
print("Hidden size 768: PASS")
print("5-second causal context: PASS")
print("Native sample rate 24000 Hz: PASS")
print("Candidate layers 4/8/12: PASS")
print("Mean pooling: PASS")
print("Ridge configuration: PASS")
print("Validation-only selection: PASS")
print("TEST lock: PASS")

print(
    "\nRESULT: PASS - MERT baseline design "
    "matches frozen experiment protocol"
)