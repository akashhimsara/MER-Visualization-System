"""
Numerical Context Vector Builder for Personalization (LinUCB).

Extracts continuous emotion dimensions (valence, arousal) from MER Tier 3 events
and constructs a fixed-dimension numerical context vector for contextual bandit arm selection.
"""

from typing import Any, Dict, List

DEFAULT_BIAS_TERM: float = 1.0
FEATURE_NAMES: List[str] = ["valence", "arousal", "bias"]
CONTEXT_DIMENSION: int = 3


class ContextVector(dict):
    """
    Structured numerical context representation for contextual bandit algorithms (LinUCB).
    Inherits from dict for JSON serialization compatibility and convenient key access,
    while also providing typed attribute access and list conversion.

    Note:
    To avoid shadowing the built-in dict.values() method, the numerical vector is exposed
    via the typed properties .vector and .vector_values, while the dictionary key "values"
    is preserved for contract and JSON compatibility.
    """

    def __init__(
        self,
        feature_names: List[str],
        values: List[float],
        dimension: int,
    ):
        super().__init__(
            feature_names=feature_names,
            values=values,
            dimension=dimension,
        )

    @property
    def feature_names(self) -> List[str]:
        return self["feature_names"]

    @property
    def vector(self) -> List[float]:
        """Return the numerical context vector values without shadowing dict.values()."""
        return self["values"]

    @property
    def vector_values(self) -> List[float]:
        """Alias for .vector to access numerical feature values."""
        return self["values"]

    @property
    def dimension(self) -> int:
        return self["dimension"]

    def to_list(self) -> List[float]:
        """Return the numerical feature values as a standard Python list."""
        return list(self["values"])

    @property
    def valence(self) -> float:
        return self["values"][0]

    @property
    def arousal(self) -> float:
        return self["values"][1]

    @property
    def bias(self) -> float:
        return self["values"][2]


def build_context_vector(tier3_event: Dict[str, Any]) -> ContextVector:
    """
    Extract continuous valence and arousal from a MER Tier 3 event and construct
    the standard 3-dimensional context vector: [valence, arousal, bias].

    Args:
        tier3_event: Dictionary conforming to Contract v1.1 mer-tier3.schema.json.

    Returns:
        ContextVector containing feature_names, numerical values, and dimension.
    """
    emotion = tier3_event["emotion"]
    valence = float(emotion["valence"])
    arousal = float(emotion["arousal"])
    bias = DEFAULT_BIAS_TERM

    values = [valence, arousal, bias]

    return ContextVector(
        feature_names=list(FEATURE_NAMES),
        values=values,
        dimension=CONTEXT_DIMENSION,
    )
