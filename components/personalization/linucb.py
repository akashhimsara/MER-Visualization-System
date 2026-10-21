"""
Disjoint Linear Upper Confidence Bound (LinUCB) Personalization Core.

Maintains independent ridge regression state (A_a, b_a) for each candidate arm
to balance exploitation (predicted expected reward) and exploration (uncertainty).
Consumes numerical context vectors [valence, arousal, bias] and provides
deterministic arm selection.
"""

import math
from typing import Any, Dict, List, Optional, Sequence
import numpy as np

DEFAULT_ALPHA: float = 1.0


class LinUCBSelection(dict):
    """
    Structured outcome of LinUCB arm selection.
    Inherits from dict for serialization compatibility and convenient key access,
    while also providing typed attribute access.
    """

    def __init__(
        self,
        selected_arm: str,
        selected_score: float,
        arm_scores: Dict[str, float],
        exploitation_scores: Optional[Dict[str, float]] = None,
        exploration_scores: Optional[Dict[str, float]] = None,
    ):
        super().__init__(
            selected_arm=selected_arm,
            selected_score=selected_score,
            arm_scores=arm_scores,
            exploitation_scores=exploitation_scores or {},
            exploration_scores=exploration_scores or {},
        )

    @property
    def selected_arm(self) -> str:
        return self["selected_arm"]

    @property
    def selected_score(self) -> float:
        return self["selected_score"]

    @property
    def arm_scores(self) -> Dict[str, float]:
        return self["arm_scores"]

    @property
    def exploitation_scores(self) -> Dict[str, float]:
        return self["exploitation_scores"]

    @property
    def exploration_scores(self) -> Dict[str, float]:
        return self["exploration_scores"]


class LinUCB:
    """
    Standard disjoint LinUCB contextual bandit algorithm (Li et al., 2010).

    For each arm a:
        A_a = d x d matrix, initialized to I_d
        b_a = d vector, initialized to 0_d

    At each decision step given context vector x:
        theta_a = A_a^{-1} b_a (solved via np.linalg.solve)
        exploitation = theta_a^T x
        exploration = alpha * sqrt(x^T A_a^{-1} x)
        score_a = exploitation + exploration
        selected_arm = argmax_a score_a (deterministic tie-breaking: first arm wins)

    On reward feedback r for chosen arm a:
        A_a <- A_a + x x^T
        b_a <- b_a + r x
    """

    def __init__(
        self,
        arms: Sequence[str],
        context_dimension: int = 3,
        alpha: float = DEFAULT_ALPHA,
    ):
        if not arms:
            raise ValueError("LinUCB requires at least one arm.")
        if context_dimension <= 0:
            raise ValueError("context_dimension must be a positive integer.")
        if alpha < 0:
            raise ValueError("alpha exploration parameter must be non-negative.")

        self.arms: List[str] = list(arms)
        self.context_dimension: int = int(context_dimension)
        self.alpha: float = float(alpha)

        # Disjoint model state per arm
        self.A: Dict[str, np.ndarray] = {
            arm: np.identity(self.context_dimension, dtype=np.float64)
            for arm in self.arms
        }
        self.b: Dict[str, np.ndarray] = {
            arm: np.zeros(self.context_dimension, dtype=np.float64)
            for arm in self.arms
        }

    def ensure_arm(self, arm: str) -> None:
        """
        Dynamically ensure a visual/preset arm exists in the LinUCB model.
        If the arm is new, initializes A_a = I_d and b_a = 0_d.
        If the arm already exists, preserves existing ridge regression state (A_a, b_a)
        and historical learning exactly.
        """
        if arm is None:
            raise ValueError("arm cannot be None.")
        clean_arm = str(arm).strip()
        if not clean_arm:
            raise ValueError("arm cannot be empty or whitespace-only.")
        if clean_arm not in self.A:
            self.A[clean_arm] = np.identity(self.context_dimension, dtype=np.float64)
            self.b[clean_arm] = np.zeros(self.context_dimension, dtype=np.float64)
            if clean_arm not in self.arms:
                self.arms.append(clean_arm)

    def ensure_arms(self, arms: Sequence[str]) -> None:
        """
        Ensure multiple visual/preset arms exist in the LinUCB model,
        preserving any existing learned arms.
        """
        for arm in arms:
            self.ensure_arm(arm)

    def _extract_vector(self, context_vector: Any) -> np.ndarray:
        """
        Validate and convert context input into a 1D float64 NumPy array.
        Accepts ContextVector instances, lists, tuples, or NumPy arrays.
        """
        if isinstance(context_vector, dict) and "values" in context_vector:
            raw = context_vector["values"]
        elif hasattr(context_vector, "to_list") and callable(context_vector.to_list):
            raw = context_vector.to_list()
        elif hasattr(context_vector, "vector"):
            raw = context_vector.vector
        elif isinstance(context_vector, (list, tuple, np.ndarray)):
            raw = context_vector
        else:
            raise ValueError(
                f"Unsupported context vector type: {type(context_vector).__name__}"
            )

        arr = np.asarray(raw, dtype=np.float64)
        if arr.ndim != 1 or arr.shape[0] != self.context_dimension:
            raise ValueError(
                f"Expected 1D context vector of dimension {self.context_dimension}, "
                f"got shape {arr.shape}."
            )
        return arr

    def select_arm(
        self,
        context_vector: Any,
        eligible_arms: Optional[Sequence[str]] = None,
    ) -> LinUCBSelection:
        """
        Score candidate arms and select the one with the maximum LinUCB score.
        If eligible_arms is provided, scores ONLY arms within eligible_arms.
        If eligible_arms is None, scores all initialized arms in self.arms.

        Tie-breaking: deterministic, first arm among equal maximum scores wins.
        """
        if eligible_arms is not None:
            if len(eligible_arms) == 0:
                raise ValueError("eligible_arms cannot be empty.")
            # Normalize and validate candidate arms
            candidate_list: List[str] = []
            for arm in eligible_arms:
                if arm is None:
                    raise ValueError("eligible arm cannot be None.")
                clean_arm = str(arm).strip()
                if not clean_arm:
                    raise ValueError("eligible arm cannot be empty or whitespace-only.")
                if clean_arm not in candidate_list:
                    candidate_list.append(clean_arm)
            self.ensure_arms(candidate_list)
            target_arms = candidate_list
        else:
            target_arms = self.arms

        x = self._extract_vector(context_vector)

        arm_scores: Dict[str, float] = {}
        exploitation_scores: Dict[str, float] = {}
        exploration_scores: Dict[str, float] = {}

        best_arm: Optional[str] = None
        best_score: float = -float("inf")

        for arm in target_arms:
            A_a = self.A[arm]
            b_a = self.b[arm]

            # Solve linear system A_a @ theta_a = b_a for theta_a (numerically stable inverse)
            theta_a = np.linalg.solve(A_a, b_a)

            # Solve linear system A_a @ v = x for v, so x^T @ A_a^{-1} @ x == x^T @ v
            v = np.linalg.solve(A_a, x)

            exploitation = float(np.dot(theta_a, x))
            variance = float(np.dot(x, v))
            exploration = self.alpha * math.sqrt(max(0.0, variance))

            score = exploitation + exploration

            arm_scores[arm] = score
            exploitation_scores[arm] = exploitation
            exploration_scores[arm] = exploration

            # Strict inequality: preserves first arm on ties (deterministic tie-breaking)
            if score > best_score:
                best_score = score
                best_arm = arm

        return LinUCBSelection(
            selected_arm=best_arm,
            selected_score=best_score,
            arm_scores=arm_scores,
            exploitation_scores=exploitation_scores,
            exploration_scores=exploration_scores,
        )

    def update(
        self,
        arm_id: str,
        context_vector: Any,
        reward: float,
    ) -> None:
        """
        Update the ridge regression statistics (A_a and b_a) for the chosen arm.

        A_a <- A_a + x x^T
        b_a <- b_a + r x
        """
        if arm_id not in self.A:
            raise ValueError(f"Unknown arm_id '{arm_id}'. Valid arms: {self.arms}")

        x = self._extract_vector(context_vector)
        r = float(reward)

        self.A[arm_id] += np.outer(x, x)
        self.b[arm_id] += r * x
