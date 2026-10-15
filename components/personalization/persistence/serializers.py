"""
Serialization and Deserialization Helpers for Personalization Persistence.

Converts between in-memory models (LinUCB, UserPersonalizationState, PresetStats)
and portable JSON-serializable dictionaries with strict shape and type validation.
Does NOT use unsafe pickle.
"""

from typing import Any, Dict, List, Sequence, Tuple
import numpy as np

from components.personalization.linucb import DEFAULT_ALPHA, LinUCB
from components.personalization.user_state import (
    DEFAULT_MAX_HISTORY_SIZE,
    PresetStats,
    UserPersonalizationState,
)


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize objects to guarantee 100% JSON compliance:
    converts NumPy scalars/arrays to standard Python primitives.
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# LinUCB Serialization
# ---------------------------------------------------------------------------

def serialize_linucb_arm(
    arm_id: str,
    A_a: np.ndarray,
    b_a: np.ndarray,
    context_dimension: int,
    alpha: float,
) -> Dict[str, Any]:
    """Serialize a single LinUCB arm's ridge regression state to pure Python primitives."""
    if A_a.shape != (context_dimension, context_dimension):
        raise ValueError(
            f"Invalid A matrix shape for arm '{arm_id}': expected "
            f"({context_dimension}, {context_dimension}), got {A_a.shape}"
        )
    if b_a.shape != (context_dimension,):
        raise ValueError(
            f"Invalid b vector shape for arm '{arm_id}': expected "
            f"({context_dimension},), got {b_a.shape}"
        )
    return {
        "arm_id": arm_id,
        "context_dimension": int(context_dimension),
        "alpha": float(alpha),
        "a_matrix": [[float(val) for val in row] for row in A_a],
        "b_vector": [float(val) for val in b_a],
    }


def deserialize_linucb_arm(
    data: Dict[str, Any],
    expected_dimension: int = 3,
) -> Tuple[str, np.ndarray, np.ndarray]:
    """
    Deserialize a LinUCB arm's state, validating matrix and vector dimensions.
    Returns (arm_id, A_matrix, b_vector).
    """
    arm_id = str(data["arm_id"])
    a_raw = data["a_matrix"]
    b_raw = data["b_vector"]

    A_arr = np.asarray(a_raw, dtype=np.float64)
    b_arr = np.asarray(b_raw, dtype=np.float64)

    if A_arr.ndim != 2 or A_arr.shape != (expected_dimension, expected_dimension):
        raise ValueError(
            f"Corrupted or invalid A matrix shape for arm '{arm_id}': "
            f"expected ({expected_dimension}, {expected_dimension}), got {A_arr.shape}"
        )
    if b_arr.ndim != 1 or b_arr.shape != (expected_dimension,):
        raise ValueError(
            f"Corrupted or invalid b vector shape for arm '{arm_id}': "
            f"expected ({expected_dimension},), got {b_arr.shape}"
        )

    return arm_id, A_arr, b_arr


def serialize_linucb_model(model: LinUCB) -> Dict[str, Any]:
    """Serialize a complete LinUCB instance to a JSON-compatible dictionary."""
    return {
        "context_dimension": model.context_dimension,
        "alpha": float(model.alpha),
        "arms": [
            serialize_linucb_arm(
                arm_id=arm,
                A_a=model.A[arm],
                b_a=model.b[arm],
                context_dimension=model.context_dimension,
                alpha=model.alpha,
            )
            for arm in model.arms
        ],
    }


def deserialize_linucb_model(data: Dict[str, Any]) -> LinUCB:
    """Reconstruct a LinUCB instance from serialized dictionary data."""
    context_dimension = int(data["context_dimension"])
    alpha = float(data.get("alpha", DEFAULT_ALPHA))
    arms_data = data["arms"]

    if not arms_data:
        raise ValueError("Cannot deserialize LinUCB model with zero arms.")

    arm_ids = [arm_info["arm_id"] for arm_info in arms_data]
    model = LinUCB(arms=arm_ids, context_dimension=context_dimension, alpha=alpha)

    for arm_info in arms_data:
        arm_id, A_arr, b_arr = deserialize_linucb_arm(arm_info, expected_dimension=context_dimension)
        model.A[arm_id] = A_arr
        model.b[arm_id] = b_arr

    return model


# ---------------------------------------------------------------------------
# User State Serialization
# ---------------------------------------------------------------------------

def serialize_user_state(state: UserPersonalizationState) -> Dict[str, Any]:
    """Serialize a UserPersonalizationState instance to a JSON-sanitized dictionary."""
    return sanitize_for_json(state.to_dict())


def deserialize_user_state(data: Dict[str, Any]) -> UserPersonalizationState:
    """Reconstruct a UserPersonalizationState instance from dictionary data."""
    return UserPersonalizationState.from_dict(data)
