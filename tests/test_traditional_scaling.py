from pathlib import Path

import numpy as np
from sklearn.preprocessing import StandardScaler


FEATURE_PATH = Path(
    "data/processed/deam_traditional_features_v1.npz"
)


print("===== TRADITIONAL TRAIN-ONLY SCALING TEST =====")

artifact = np.load(
    FEATURE_PATH,
    allow_pickle=False,
)

X = artifact["X"]
split = artifact["split"].astype(str)

train_mask = split == "train"
val_mask = split == "validation"
test_mask = split == "test"

X_train = X[train_mask]
X_val = X[val_mask]

print("\nRaw partitions")
print("TRAIN:", X_train.shape)
print("VALIDATION:", X_val.shape)
print("LOCKED TEST rows:", int(test_mask.sum()))

# ---------------------------------------------------------
# IMPORTANT:
# scaler is fitted ONLY using TRAIN.
# ---------------------------------------------------------

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(
    X_train
)

X_val_scaled = scaler.transform(
    X_val
)


print("\nScaled partitions")
print("TRAIN:", X_train_scaled.shape)
print("VALIDATION:", X_val_scaled.shape)

print(
    "TRAIN finite:",
    np.isfinite(X_train_scaled).all()
)

print(
    "VALIDATION finite:",
    np.isfinite(X_val_scaled).all()
)


# StandardScaler should make TRAIN feature means
# approximately zero.

max_abs_train_mean = float(
    np.max(
        np.abs(
            X_train_scaled.mean(axis=0)
        )
    )
)

print(
    "\nMaximum absolute scaled TRAIN feature mean:",
    max_abs_train_mean
)


print("\nScaler evidence")
print(
    "Scaler n_samples_seen_:",
    scaler.n_samples_seen_
)

print(
    "Expected TRAIN rows:",
    X_train.shape[0]
)


valid = (
    X_train.shape == (88153, 86)
    and X_val.shape == (19965, 86)
    and int(test_mask.sum()) == 21877
    and scaler.n_samples_seen_ == 88153
    and np.isfinite(X_train_scaled).all()
    and np.isfinite(X_val_scaled).all()
)


if valid:
    print(
        "\nRESULT: PASS - StandardScaler was fitted "
        "using TRAIN only; TEST remains untouched"
    )
else:
    print("\nRESULT: REVIEW REQUIRED")