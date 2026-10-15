"""
User Personalization State and History Tracking Layer.

Maintains structured, in-memory per-user interaction history, per-preset statistics,
and preference summaries prior to PostgreSQL database persistence.
Keeps interaction statistics strictly decoupled from LinUCB mathematical state (A_a, b_a).
"""

from typing import Any, Dict, List, Optional, Sequence
from components.personalization.presets import MOCK_ARM_PRESETS

DEFAULT_MAX_HISTORY_SIZE: int = 20


class PresetStats(dict):
    """
    Per-preset interaction and reward statistics.
    Inherits from dict for serialization compatibility and convenient key access,
    while also providing typed attribute access and property calculation.
    """

    def __init__(self, preset_id: str):
        super().__init__(
            preset_id=preset_id,
            recommendation_count=0,
            feedback_count=0,
            like_count=0,
            dislike_count=0,
            rating_count=0,
            rating_sum=0.0,
            preset_select_count=0,
            preset_skip_count=0,
            cumulative_reward=0.0,
            numerical_reward_count=0,
            view_duration_count=0,
            total_duration_ms=0,
        )

    @property
    def preset_id(self) -> str:
        return self["preset_id"]

    @property
    def recommendation_count(self) -> int:
        return self["recommendation_count"]

    @recommendation_count.setter
    def recommendation_count(self, val: int):
        self["recommendation_count"] = int(val)

    @property
    def feedback_count(self) -> int:
        return self["feedback_count"]

    @feedback_count.setter
    def feedback_count(self, val: int):
        self["feedback_count"] = int(val)

    @property
    def like_count(self) -> int:
        return self["like_count"]

    @like_count.setter
    def like_count(self, val: int):
        self["like_count"] = int(val)

    @property
    def dislike_count(self) -> int:
        return self["dislike_count"]

    @dislike_count.setter
    def dislike_count(self, val: int):
        self["dislike_count"] = int(val)

    @property
    def rating_count(self) -> int:
        return self["rating_count"]

    @rating_count.setter
    def rating_count(self, val: int):
        self["rating_count"] = int(val)

    @property
    def rating_sum(self) -> float:
        return self["rating_sum"]

    @rating_sum.setter
    def rating_sum(self, val: float):
        self["rating_sum"] = float(val)

    @property
    def preset_select_count(self) -> int:
        return self["preset_select_count"]

    @preset_select_count.setter
    def preset_select_count(self, val: int):
        self["preset_select_count"] = int(val)

    @property
    def preset_skip_count(self) -> int:
        return self["preset_skip_count"]

    @preset_skip_count.setter
    def preset_skip_count(self, val: int):
        self["preset_skip_count"] = int(val)

    @property
    def cumulative_reward(self) -> float:
        return self["cumulative_reward"]

    @cumulative_reward.setter
    def cumulative_reward(self, val: float):
        self["cumulative_reward"] = float(val)

    @property
    def numerical_reward_count(self) -> int:
        return self["numerical_reward_count"]

    @numerical_reward_count.setter
    def numerical_reward_count(self, val: int):
        self["numerical_reward_count"] = int(val)

    @property
    def view_duration_count(self) -> int:
        return self["view_duration_count"]

    @view_duration_count.setter
    def view_duration_count(self, val: int):
        self["view_duration_count"] = int(val)

    @property
    def total_duration_ms(self) -> int:
        return self["total_duration_ms"]

    @total_duration_ms.setter
    def total_duration_ms(self, val: int):
        self["total_duration_ms"] = int(val)

    @property
    def average_rating(self) -> Optional[float]:
        if self["rating_count"] == 0:
            return None
        return round(self["rating_sum"] / self["rating_count"], 4)

    @property
    def average_reward(self) -> Optional[float]:
        if self["numerical_reward_count"] == 0:
            return None
        return round(self["cumulative_reward"] / self["numerical_reward_count"], 4)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary of per-preset statistics."""
        return {
            "preset_id": self.preset_id,
            "recommendation_count": self.recommendation_count,
            "feedback_count": self.feedback_count,
            "like_count": self.like_count,
            "dislike_count": self.dislike_count,
            "rating_count": self.rating_count,
            "rating_sum": self.rating_sum,
            "average_rating": self.average_rating,
            "preset_select_count": self.preset_select_count,
            "preset_skip_count": self.preset_skip_count,
            "cumulative_reward": round(self.cumulative_reward, 4),
            "numerical_reward_count": self.numerical_reward_count,
            "average_reward": self.average_reward,
            "view_duration_count": self.view_duration_count,
            "total_duration_ms": self.total_duration_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresetStats":
        stats = cls(data["preset_id"])
        stats.recommendation_count = int(data.get("recommendation_count", 0))
        stats.feedback_count = int(data.get("feedback_count", 0))
        stats.like_count = int(data.get("like_count", 0))
        stats.dislike_count = int(data.get("dislike_count", 0))
        stats.rating_count = int(data.get("rating_count", 0))
        stats.rating_sum = float(data.get("rating_sum", 0.0))
        stats.preset_select_count = int(data.get("preset_select_count", 0))
        stats.preset_skip_count = int(data.get("preset_skip_count", 0))
        stats.cumulative_reward = float(data.get("cumulative_reward", 0.0))
        stats.numerical_reward_count = int(data.get("numerical_reward_count", 0))
        stats.view_duration_count = int(data.get("view_duration_count", 0))
        stats.total_duration_ms = int(data.get("total_duration_ms", 0))
        return stats


class UserPersonalizationState:
    """
    Structured user personalization state tracking recommendation history,
    user feedback, cumulative reward metrics, and high-level preferences.

    Maintains interaction records in bounded circular lists to prevent memory leaks.
    """

    def __init__(
        self,
        user_id: str = "user-default",
        max_history_size: int = DEFAULT_MAX_HISTORY_SIZE,
        presets: Optional[Sequence[str]] = None,
    ):
        self.user_id: str = str(user_id)
        self.max_history_size: int = max(1, int(max_history_size))

        self.recommendation_count: int = 0
        self.feedback_count: int = 0
        self.successful_learning_updates: int = 0

        self.last_recommended_preset: Optional[str] = None
        self.last_feedback_type: Optional[str] = None

        self.cumulative_reward: float = 0.0
        self.numerical_reward_count: int = 0

        self.preset_stats: Dict[str, PresetStats] = {
            pid: PresetStats(pid) for pid in (presets or MOCK_ARM_PRESETS)
        }

        self.recent_recommendations: List[Dict[str, Any]] = []
        self.recent_feedback: List[Dict[str, Any]] = []

    @property
    def average_reward(self) -> Optional[float]:
        """Average reward across all numerical feedback events, or None if no feedback."""
        if self.numerical_reward_count == 0:
            return None
        return round(self.cumulative_reward / self.numerical_reward_count, 4)

    def get_preset_stats(self, preset_id: str) -> PresetStats:
        """Retrieve or lazily initialize statistics for a specific preset ID."""
        if preset_id not in self.preset_stats:
            self.preset_stats[preset_id] = PresetStats(preset_id)
        return self.preset_stats[preset_id]

    def record_recommendation(
        self,
        preset_id: str,
        recommendation_id: str,
        session_id: str,
        audio_time_ms: int,
        strategy: str,
        score: Optional[float] = None,
        sequence: Optional[int] = None,
    ) -> None:
        """Record an emitted recommendation into user state and bounded history."""
        self.recommendation_count += 1
        self.last_recommended_preset = preset_id

        stats = self.get_preset_stats(preset_id)
        stats.recommendation_count += 1

        record = {
            "recommendation_id": recommendation_id,
            "preset_id": preset_id,
            "session_id": session_id,
            "audio_time_ms": audio_time_ms,
            "strategy": strategy,
            "score": score,
            "sequence": sequence,
        }
        self.recent_recommendations.append(record)
        if len(self.recent_recommendations) > self.max_history_size:
            self.recent_recommendations.pop(0)

    def record_feedback(
        self,
        feedback_type: str,
        preset_id: str,
        session_id: str,
        reward: Optional[float],
        feedback_id: Optional[str] = None,
        recommendation_id: Optional[str] = None,
        raw_value: Optional[Any] = None,
        is_auxiliary: bool = False,
    ) -> None:
        """Record a processed feedback event into user state and bounded history."""
        self.feedback_count += 1
        self.last_feedback_type = feedback_type

        stats = self.get_preset_stats(preset_id)
        stats.feedback_count += 1

        if feedback_type == "like":
            stats.like_count += 1
        elif feedback_type == "dislike":
            stats.dislike_count += 1
        elif feedback_type == "rating":
            stats.rating_count += 1
            if raw_value is not None:
                stats.rating_sum += float(raw_value)
        elif feedback_type == "preset_select":
            stats.preset_select_count += 1
        elif feedback_type == "preset_skip":
            stats.preset_skip_count += 1
        elif feedback_type == "view_duration":
            stats.view_duration_count += 1
            if raw_value is not None:
                stats.total_duration_ms += int(raw_value)

        if reward is not None and not is_auxiliary:
            r = float(reward)
            self.cumulative_reward += r
            self.numerical_reward_count += 1
            self.successful_learning_updates += 1

            stats.cumulative_reward += r
            stats.numerical_reward_count += 1

        record = {
            "feedback_id": feedback_id,
            "feedback_type": feedback_type,
            "preset_id": preset_id,
            "session_id": session_id,
            "reward": reward,
            "raw_value": raw_value,
            "is_auxiliary": is_auxiliary,
            "recommendation_id": recommendation_id,
        }
        self.recent_feedback.append(record)
        if len(self.recent_feedback) > self.max_history_size:
            self.recent_feedback.pop(0)

    def get_most_positively_rewarded_preset(self) -> Optional[str]:
        """
        Preset with highest cumulative positive reward.
        Deterministic tie-breaking: cumulative_reward desc, average_reward desc, preset_id asc.
        """
        candidates = [s for s in self.preset_stats.values() if s.cumulative_reward > 0.0]
        if not candidates:
            return None
        candidates.sort(key=lambda s: (-s.cumulative_reward, -(s.average_reward or 0.0), s.preset_id))
        return candidates[0].preset_id

    def get_most_frequently_selected_preset(self) -> Optional[str]:
        """
        Preset with highest preset_select_count.
        Deterministic tie-breaking: count desc, preset_id asc.
        """
        candidates = [s for s in self.preset_stats.values() if s.preset_select_count > 0]
        if not candidates:
            return None
        candidates.sort(key=lambda s: (-s.preset_select_count, s.preset_id))
        return candidates[0].preset_id

    def get_most_frequently_liked_preset(self) -> Optional[str]:
        """
        Preset with highest like_count.
        Deterministic tie-breaking: count desc, preset_id asc.
        """
        candidates = [s for s in self.preset_stats.values() if s.like_count > 0]
        if not candidates:
            return None
        candidates.sort(key=lambda s: (-s.like_count, s.preset_id))
        return candidates[0].preset_id

    def get_average_observed_reward(self) -> Optional[float]:
        """Average reward across all numerical feedback, or None if no numerical feedback."""
        return self.average_reward

    def is_beyond_cold_start(self, min_updates: int = 1) -> bool:
        """Returns True if the user has accumulated at least min_updates learning updates."""
        return self.successful_learning_updates >= min_updates

    def get_preference_summary(self) -> Dict[str, Any]:
        """High-level summary of user preferences and interaction volume."""
        return {
            "user_id": self.user_id,
            "recommendation_count": self.recommendation_count,
            "feedback_count": self.feedback_count,
            "successful_learning_updates": self.successful_learning_updates,
            "average_observed_reward": self.get_average_observed_reward(),
            "most_positively_rewarded_preset": self.get_most_positively_rewarded_preset(),
            "most_frequently_selected_preset": self.get_most_frequently_selected_preset(),
            "most_frequently_liked_preset": self.get_most_frequently_liked_preset(),
            "is_beyond_cold_start": self.is_beyond_cold_start(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Produce a JSON-serializable dictionary representation of the user state
        for future PostgreSQL storage and API consumption.
        """
        return {
            "user_id": self.user_id,
            "max_history_size": self.max_history_size,
            "recommendation_count": self.recommendation_count,
            "feedback_count": self.feedback_count,
            "successful_learning_updates": self.successful_learning_updates,
            "last_recommended_preset": self.last_recommended_preset,
            "last_feedback_type": self.last_feedback_type,
            "cumulative_reward": round(self.cumulative_reward, 4),
            "numerical_reward_count": self.numerical_reward_count,
            "average_reward": self.average_reward,
            "preference_summary": self.get_preference_summary(),
            "preset_stats": {
                pid: stats.to_dict() for pid, stats in self.preset_stats.items()
            },
            "recent_recommendations": list(self.recent_recommendations),
            "recent_feedback": list(self.recent_feedback),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPersonalizationState":
        """Reconstruct UserPersonalizationState from a dictionary."""
        user_id = data["user_id"]
        max_history_size = int(data.get("max_history_size", DEFAULT_MAX_HISTORY_SIZE))
        state = cls(user_id=user_id, max_history_size=max_history_size)

        state.recommendation_count = int(data.get("recommendation_count", 0))
        state.feedback_count = int(data.get("feedback_count", 0))
        state.successful_learning_updates = int(data.get("successful_learning_updates", 0))
        state.last_recommended_preset = data.get("last_recommended_preset")
        state.last_feedback_type = data.get("last_feedback_type")
        state.cumulative_reward = float(data.get("cumulative_reward", 0.0))
        state.numerical_reward_count = int(data.get("numerical_reward_count", 0))

        preset_stats_data = data.get("preset_stats", {})
        for pid, pdata in preset_stats_data.items():
            state.preset_stats[pid] = PresetStats.from_dict(pdata)

        state.recent_recommendations = list(data.get("recent_recommendations", []))
        state.recent_feedback = list(data.get("recent_feedback", []))
        return state
