"""
PostgreSQL Persistence Layer for Personalization & User Analytics.
"""

from components.personalization.persistence.database import (
    DEFAULT_DATABASE_URL,
    create_db_engine,
    get_database_url,
    get_session_factory,
)
from components.personalization.persistence.models import (
    Base,
    PersonalizationInteractionModel,
    PersonalizationLinUCBStateModel,
    PersonalizationPresetStatsModel,
    PersonalizationProcessedFeedbackModel,
    PersonalizationUserStateModel,
)
from components.personalization.persistence.repository import PersonalizationRepository
from components.personalization.persistence.serializers import (
    deserialize_linucb_arm,
    deserialize_linucb_model,
    deserialize_user_state,
    sanitize_for_json,
    serialize_linucb_arm,
    serialize_linucb_model,
    serialize_user_state,
)
from components.personalization.persistence.service import (
    persist_adaptive_engine,
    restore_adaptive_engine,
)

__all__ = [
    # Database
    "DEFAULT_DATABASE_URL",
    "get_database_url",
    "create_db_engine",
    "get_session_factory",
    # Models
    "Base",
    "PersonalizationUserStateModel",
    "PersonalizationPresetStatsModel",
    "PersonalizationLinUCBStateModel",
    "PersonalizationInteractionModel",
    "PersonalizationProcessedFeedbackModel",
    # Serializers
    "sanitize_for_json",
    "serialize_linucb_arm",
    "deserialize_linucb_arm",
    "serialize_linucb_model",
    "deserialize_linucb_model",
    "serialize_user_state",
    "deserialize_user_state",
    # Repository & Service
    "PersonalizationRepository",
    "restore_adaptive_engine",
    "persist_adaptive_engine",
]
