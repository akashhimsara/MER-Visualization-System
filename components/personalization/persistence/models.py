"""
SQLAlchemy ORM Models for Personalization & LinUCB Persistence.

Tables:
- personalization_user_state: Summary counters, reward aggregates, and timestamps.
- personalization_preset_stats: Per-preset interaction metrics with (user_id, preset_id) uniqueness.
- personalization_linucb_state: LinUCB design covariance matrices (A_a) and vectors (b_a) per arm.
- personalization_interactions: Emitted recommendation records and associated context vectors.
- personalization_processed_feedback: Idempotency log of processed user feedback events.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PersonalizationUserStateModel(Base):
    """
    Persisted user personalization profile and aggregate performance.
    """
    __tablename__ = "personalization_user_state"

    user_id = Column(String(128), primary_key=True)
    recommendation_count = Column(Integer, default=0, nullable=False)
    feedback_count = Column(Integer, default=0, nullable=False)
    successful_learning_updates = Column(Integer, default=0, nullable=False)
    last_recommended_preset = Column(String(128), nullable=True)
    last_feedback_type = Column(String(64), nullable=True)
    cumulative_reward = Column(Float, default=0.0, nullable=False)
    numerical_reward_count = Column(Integer, default=0, nullable=False)
    max_history_size = Column(Integer, default=20, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    preset_stats = relationship(
        "PersonalizationPresetStatsModel",
        back_populates="user_state",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PersonalizationPresetStatsModel(Base):
    """
    Per-preset interaction metrics and reward performance for a user.
    """
    __tablename__ = "personalization_preset_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(128),
        ForeignKey("personalization_user_state.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    preset_id = Column(String(128), nullable=False, index=True)
    recommendation_count = Column(Integer, default=0, nullable=False)
    feedback_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    dislike_count = Column(Integer, default=0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    rating_sum = Column(Float, default=0.0, nullable=False)
    preset_select_count = Column(Integer, default=0, nullable=False)
    preset_skip_count = Column(Integer, default=0, nullable=False)
    cumulative_reward = Column(Float, default=0.0, nullable=False)
    numerical_reward_count = Column(Integer, default=0, nullable=False)
    view_duration_count = Column(Integer, default=0, nullable=False)
    total_duration_ms = Column(Integer, default=0, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "preset_id", name="uq_user_preset_stats"),
    )

    user_state = relationship("PersonalizationUserStateModel", back_populates="preset_stats")


class PersonalizationLinUCBStateModel(Base):
    """
    Persisted LinUCB ridge regression parameters (A matrix and b vector) per arm.
    """
    __tablename__ = "personalization_linucb_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    arm_id = Column(String(128), nullable=False, index=True)
    context_dimension = Column(Integer, default=3, nullable=False)
    alpha = Column(Float, default=1.0, nullable=False)
    a_matrix = Column(JSON, nullable=False)  # Shape (d, d) portable JSON list of lists
    b_vector = Column(JSON, nullable=False)  # Shape (d,) portable JSON list
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "arm_id", name="uq_user_arm_linucb"),
    )


class PersonalizationInteractionModel(Base):
    """
    Persisted recommendation events and context vectors for learning attribution.
    """
    __tablename__ = "personalization_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    preset_id = Column(String(128), nullable=False, index=True)
    audio_time_ms = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)
    context_vector = Column(JSON, nullable=False)  # Portable list of floats [valence, arousal, bias]
    strategy = Column(String(32), nullable=False)
    score = Column(Float, nullable=True)
    feedback_applied = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PersonalizationProcessedFeedbackModel(Base):
    """
    Idempotency ledger recording processed FeedbackEvents to prevent replay updates.
    """
    __tablename__ = "personalization_processed_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    preset_id = Column(String(128), nullable=False, index=True)
    feedback_type = Column(String(64), nullable=False)
    reward = Column(Float, nullable=True)
    raw_value = Column(JSON, nullable=True)
    is_auxiliary = Column(Boolean, default=False, nullable=False)
    recommendation_id = Column(String(128), nullable=True, index=True)
    processed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
