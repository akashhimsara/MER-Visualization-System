import os
import random

import numpy as np


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducible experiments.

    PyTorch-specific settings will be added after PyTorch
    is installed in the project environment.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)

    random.seed(seed)
    np.random.seed(seed)


if __name__ == "__main__":
    set_seed(42)
    print("Primary experiment seed set to 42.")