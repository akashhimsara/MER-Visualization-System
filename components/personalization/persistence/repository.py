"""
Repository Layer for Personalization State Persistence.

Abstracts database operations away from mathematical bandit algorithms and business logic.
Provides idempotent writes, consistent updates, and state retrieval.
"""

from typing import Any, Dict, List, Optional, Sequence, Set
from sqlalchemy.orm import Session, sessionmaker

from components.personalization.linucb import DEFAULT_ALPHA, LinUCB
from components.personalization.persistence.database import get_session_factory
from components.personalization.persistence.models import (
    PersonalizationInteractionModel,
    PersonalizationLinUCBStateModel,
    PersonalizationPresetStatsModel,
    PersonalizationProcessedFeedbackModel,
    PersonalizationUserStateModel,
)
from components.personalization.persistence.serializers import (
    deserialize_linucb_arm,
    deserialize_user_state,
    sanitize_for_json,
    serialize_linucb_arm,
    serialize_user_state,
)
from components.personalization.presets import MOCK_ARM_PRESETS
from components.personalization.user_state import UserPersonalizationState


class PersonalizationRepository:
    """
    Data access repository for Adaptive Personalization and LinUCB state.
    """

    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None):
        self.session_factory = session_factory or get_session_factory()

    def _get_session(self) -> Session:
        return self.session_factory()

    # -----------------------------------------------------------------------
    # User Personalization State
    # -----------------------------------------------------------------------

    def save_user_state(self, user_state: UserPersonalizationState) -> None:
        """Persist or update UserPersonalizationState and all per-preset statistics."""
        data = serialize_user_state(user_state)
        user_id = user_state.user_id

        with self._get_session() as session:
            with session.begin():
                user_record = session.get(PersonalizationUserStateModel, user_id)
                if not user_record:
                    user_record = PersonalizationUserStateModel(user_id=user_id)
                    session.add(user_record)

                user_record.recommendation_count = data["recommendation_count"]
                user_record.feedback_count = data["feedback_count"]
                user_record.successful_learning_updates = data["successful_learning_updates"]
                user_record.last_recommended_preset = data["last_recommended_preset"]
                user_record.last_feedback_type = data["last_feedback_type"]
                user_record.cumulative_reward = data["cumulative_reward"]
                user_record.numerical_reward_count = data.get("numerical_reward_count", 0)
                user_record.max_history_size = data["max_history_size"]

                # Preset statistics upsert
                for pid, pdata in data.get("preset_stats", {}).items():
                    stats_record = (
                        session.query(PersonalizationPresetStatsModel)
                        .filter_by(user_id=user_id, preset_id=pid)
                        .first()
                    )
                    if not stats_record:
                        stats_record = PersonalizationPresetStatsModel(
                            user_id=user_id, preset_id=pid
                        )
                        session.add(stats_record)

                    stats_record.recommendation_count = pdata["recommendation_count"]
                    stats_record.feedback_count = pdata["feedback_count"]
                    stats_record.like_count = pdata["like_count"]
                    stats_record.dislike_count = pdata["dislike_count"]
                    stats_record.rating_count = pdata["rating_count"]
                    stats_record.rating_sum = pdata["rating_sum"]
                    stats_record.preset_select_count = pdata["preset_select_count"]
                    stats_record.preset_skip_count = pdata["preset_skip_count"]
                    stats_record.cumulative_reward = pdata["cumulative_reward"]
                    stats_record.numerical_reward_count = pdata.get("numerical_reward_count", 0)
                    stats_record.view_duration_count = pdata["view_duration_count"]
                    stats_record.total_duration_ms = pdata["total_duration_ms"]

    def load_user_state(self, user_id: str) -> Optional[UserPersonalizationState]:
        """Load and reconstruct a UserPersonalizationState instance, or return None if not found."""
        with self._get_session() as session:
            user_record = session.get(PersonalizationUserStateModel, user_id)
            if not user_record:
                return None

            preset_stats_dict: Dict[str, Any] = {}
            for s in user_record.preset_stats:
                preset_stats_dict[s.preset_id] = {
                    "preset_id": s.preset_id,
                    "recommendation_count": s.recommendation_count,
                    "feedback_count": s.feedback_count,
                    "like_count": s.like_count,
                    "dislike_count": s.dislike_count,
                    "rating_count": s.rating_count,
                    "rating_sum": s.rating_sum,
                    "preset_select_count": s.preset_select_count,
                    "preset_skip_count": s.preset_skip_count,
                    "cumulative_reward": s.cumulative_reward,
                    "numerical_reward_count": s.numerical_reward_count,
                    "view_duration_count": s.view_duration_count,
                    "total_duration_ms": s.total_duration_ms,
                }

            # Load recent recommendations & feedbacks bounded by max_history_size
            recent_recs = (
                session.query(PersonalizationInteractionModel)
                .filter_by(user_id=user_id)
                .order_by(PersonalizationInteractionModel.created_at.desc())
                .limit(user_record.max_history_size)
                .all()
            )
            recent_fbs = (
                session.query(PersonalizationProcessedFeedbackModel)
                .filter_by(user_id=user_id)
                .order_by(PersonalizationProcessedFeedbackModel.processed_at.desc())
                .limit(user_record.max_history_size)
                .all()
            )

            state_dict = {
                "user_id": user_record.user_id,
                "max_history_size": user_record.max_history_size,
                "recommendation_count": user_record.recommendation_count,
                "feedback_count": user_record.feedback_count,
                "successful_learning_updates": user_record.successful_learning_updates,
                "last_recommended_preset": user_record.last_recommended_preset,
                "last_feedback_type": user_record.last_feedback_type,
                "cumulative_reward": user_record.cumulative_reward,
                "numerical_reward_count": user_record.numerical_reward_count,
                "preset_stats": preset_stats_dict,
                "recent_recommendations": [
                    {
                        "recommendation_id": r.recommendation_id,
                        "preset_id": r.preset_id,
                        "session_id": r.session_id,
                        "audio_time_ms": r.audio_time_ms,
                        "strategy": r.strategy,
                        "score": r.score,
                        "sequence": r.sequence,
                    }
                    for r in reversed(recent_recs)
                ],
                "recent_feedback": [
                    {
                        "feedback_id": f.feedback_id,
                        "feedback_type": f.feedback_type,
                        "preset_id": f.preset_id,
                        "session_id": f.session_id,
                        "reward": f.reward,
                        "raw_value": f.raw_value,
                        "is_auxiliary": f.is_auxiliary,
                        "recommendation_id": f.recommendation_id,
                    }
                    for f in reversed(recent_fbs)
                ],
            }
            return deserialize_user_state(state_dict)

    # -----------------------------------------------------------------------
    # LinUCB State
    # -----------------------------------------------------------------------

    def save_linucb_state(self, user_id: str, model: LinUCB) -> None:
        """Persist or update LinUCB ridge regression parameters (A and b) for all arms."""
        with self._get_session() as session:
            with session.begin():
                for arm in model.arms:
                    arm_data = serialize_linucb_arm(
                        arm_id=arm,
                        A_a=model.A[arm],
                        b_a=model.b[arm],
                        context_dimension=model.context_dimension,
                        alpha=model.alpha,
                    )
                    record = (
                        session.query(PersonalizationLinUCBStateModel)
                        .filter_by(user_id=user_id, arm_id=arm)
                        .first()
                    )
                    if not record:
                        record = PersonalizationLinUCBStateModel(
                            user_id=user_id,
                            arm_id=arm,
                        )
                        session.add(record)

                    record.context_dimension = arm_data["context_dimension"]
                    record.alpha = arm_data["alpha"]
                    record.a_matrix = arm_data["a_matrix"]
                    record.b_vector = arm_data["b_vector"]

    def load_linucb_state(
        self,
        user_id: str,
        expected_dimension: int = 3,
        fallback_alpha: float = DEFAULT_ALPHA,
    ) -> Optional[LinUCB]:
        """Load and reconstruct LinUCB instance for user_id. Returns None if unpersisted."""
        with self._get_session() as session:
            records = (
                session.query(PersonalizationLinUCBStateModel)
                .filter_by(user_id=user_id)
                .all()
            )
            if not records:
                return None

            arm_ids = [r.arm_id for r in records]
            alpha = records[0].alpha if records else fallback_alpha
            d = records[0].context_dimension if records else expected_dimension

            model = LinUCB(arms=arm_ids, context_dimension=d, alpha=alpha)

            for r in records:
                arm_id, A_arr, b_arr = deserialize_linucb_arm(
                    {
                        "arm_id": r.arm_id,
                        "a_matrix": r.a_matrix,
                        "b_vector": r.b_vector,
                    },
                    expected_dimension=d,
                )
                model.A[arm_id] = A_arr
                model.b[arm_id] = b_arr

            return model

    # -----------------------------------------------------------------------
    # Interactions
    # -----------------------------------------------------------------------

    def save_interaction(self, interaction: Dict[str, Any], user_id: str) -> None:
        """Persist an emitted recommendation interaction."""
        with self._get_session() as session:
            with session.begin():
                rec_id = interaction["recommendation_id"]
                existing = session.query(PersonalizationInteractionModel).filter_by(recommendation_id=rec_id).first()
                if not existing:
                    record = PersonalizationInteractionModel(
                        recommendation_id=rec_id,
                        user_id=user_id,
                        session_id=interaction["session_id"],
                        preset_id=interaction["recommended_preset_id"],
                        audio_time_ms=int(interaction["audio_time_ms"]),
                        sequence=int(interaction.get("sequence", 0)),
                        context_vector=sanitize_for_json(interaction["context_vector"]),
                        strategy=interaction["strategy"],
                        score=float(interaction["score"]) if interaction.get("score") is not None else None,
                        feedback_applied=bool(interaction.get("feedback_applied", False)),
                    )
                    session.add(record)

    def mark_interaction_feedback_applied(self, recommendation_id: str) -> bool:
        """Mark a recommendation interaction as feedback_applied = True."""
        with self._get_session() as session:
            with session.begin():
                record = (
                    session.query(PersonalizationInteractionModel)
                    .filter_by(recommendation_id=recommendation_id)
                    .first()
                )
                if record:
                    record.feedback_applied = True
                    return True
                return False

    def load_pending_interactions(
        self,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load unprocessed interactions for a user (and optional session)."""
        with self._get_session() as session:
            query = session.query(PersonalizationInteractionModel).filter_by(
                user_id=user_id, feedback_applied=False
            )
            if session_id:
                query = query.filter_by(session_id=session_id)
            records = query.order_by(PersonalizationInteractionModel.created_at.asc()).all()

            return [
                {
                    "recommendation_id": r.recommendation_id,
                    "session_id": r.session_id,
                    "recommended_preset_id": r.preset_id,
                    "audio_time_ms": r.audio_time_ms,
                    "sequence": r.sequence,
                    "context_vector": r.context_vector,
                    "strategy": r.strategy,
                    "score": r.score,
                    "feedback_applied": r.feedback_applied,
                }
                for r in records
            ]

    # -----------------------------------------------------------------------
    # Processed Feedback Idempotency
    # -----------------------------------------------------------------------

    def is_feedback_processed(self, feedback_id: str) -> bool:
        """Check if feedback_id has already been recorded."""
        with self._get_session() as session:
            count = (
                session.query(PersonalizationProcessedFeedbackModel)
                .filter_by(feedback_id=feedback_id)
                .count()
            )
            return count > 0

    def save_processed_feedback(
        self,
        feedback_record: Dict[str, Any],
        user_id: str,
    ) -> bool:
        """
        Record feedback in the idempotency ledger.
        Returns True if saved, False if feedback_id is a duplicate.
        """
        feedback_id = feedback_record["feedback_id"]
        with self._get_session() as session:
            with session.begin():
                existing = (
                    session.query(PersonalizationProcessedFeedbackModel)
                    .filter_by(feedback_id=feedback_id)
                    .first()
                )
                if existing:
                    return False

                record = PersonalizationProcessedFeedbackModel(
                    feedback_id=feedback_id,
                    user_id=user_id,
                    session_id=feedback_record["session_id"],
                    preset_id=feedback_record["preset_id"],
                    feedback_type=feedback_record["feedback_type"],
                    reward=feedback_record.get("reward"),
                    raw_value=sanitize_for_json(feedback_record.get("raw_value")),
                    is_auxiliary=bool(feedback_record.get("is_auxiliary", False)),
                    recommendation_id=feedback_record.get("recommendation_id"),
                )
                session.add(record)
                return True

    def load_processed_feedback_ids(self, user_id: Optional[str] = None) -> Set[str]:
        """Load set of processed feedback IDs for duplicate protection."""
        with self._get_session() as session:
            query = session.query(PersonalizationProcessedFeedbackModel.feedback_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            return {row[0] for row in query.all()}
