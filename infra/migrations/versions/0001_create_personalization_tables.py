"""create_personalization_tables

Revision ID: 0001_personalization
Revises: None
Create Date: 2026-10-14 19:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_personalization"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. personalization_user_state
    op.create_table(
        "personalization_user_state",
        sa.Column("user_id", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("recommendation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feedback_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_learning_updates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_recommended_preset", sa.String(length=128), nullable=True),
        sa.Column("last_feedback_type", sa.String(length=64), nullable=True),
        sa.Column("cumulative_reward", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("numerical_reward_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_history_size", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # 2. personalization_preset_stats
    op.create_table(
        "personalization_preset_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey("personalization_user_state.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("preset_id", sa.String(length=128), nullable=False),
        sa.Column("recommendation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feedback_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dislike_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_sum", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("preset_select_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("preset_skip_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cumulative_reward", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("numerical_reward_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_duration_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("user_id", "preset_id", name="uq_user_preset_stats"),
    )
    op.create_index("ix_personalization_preset_stats_user_id", "personalization_preset_stats", ["user_id"])
    op.create_index("ix_personalization_preset_stats_preset_id", "personalization_preset_stats", ["preset_id"])

    # 3. personalization_linucb_state
    op.create_table(
        "personalization_linucb_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("arm_id", sa.String(length=128), nullable=False),
        sa.Column("context_dimension", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("alpha", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("a_matrix", sa.JSON(), nullable=False),
        sa.Column("b_vector", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("user_id", "arm_id", name="uq_user_arm_linucb"),
    )
    op.create_index("ix_personalization_linucb_state_user_id", "personalization_linucb_state", ["user_id"])
    op.create_index("ix_personalization_linucb_state_arm_id", "personalization_linucb_state", ["arm_id"])

    # 4. personalization_interactions
    op.create_table(
        "personalization_interactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("recommendation_id", sa.String(length=128), unique=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("preset_id", sa.String(length=128), nullable=False),
        sa.Column("audio_time_ms", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("context_vector", sa.JSON(), nullable=False),
        sa.Column("strategy", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback_applied", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_personalization_interactions_rec_id", "personalization_interactions", ["recommendation_id"])
    op.create_index("ix_personalization_interactions_user_id", "personalization_interactions", ["user_id"])
    op.create_index("ix_personalization_interactions_session_id", "personalization_interactions", ["session_id"])
    op.create_index("ix_personalization_interactions_preset_id", "personalization_interactions", ["preset_id"])

    # 5. personalization_processed_feedback
    op.create_table(
        "personalization_processed_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("feedback_id", sa.String(length=128), unique=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("preset_id", sa.String(length=128), nullable=False),
        sa.Column("feedback_type", sa.String(length=64), nullable=False),
        sa.Column("reward", sa.Float(), nullable=True),
        sa.Column("raw_value", sa.JSON(), nullable=True),
        sa.Column("is_auxiliary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recommendation_id", sa.String(length=128), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_personalization_processed_feedback_id", "personalization_processed_feedback", ["feedback_id"])
    op.create_index("ix_personalization_processed_feedback_user_id", "personalization_processed_feedback", ["user_id"])
    op.create_index("ix_personalization_processed_feedback_session_id", "personalization_processed_feedback", ["session_id"])
    op.create_index("ix_personalization_processed_feedback_preset_id", "personalization_processed_feedback", ["preset_id"])


def downgrade() -> None:
    op.drop_table("personalization_processed_feedback")
    op.drop_table("personalization_interactions")
    op.drop_table("personalization_linucb_state")
    op.drop_table("personalization_preset_stats")
    op.drop_table("personalization_user_state")
