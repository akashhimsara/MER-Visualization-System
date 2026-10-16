"""
Runtime Service for Adaptive Personalization and User Analytics.

Orchestrates multi-user AdaptivePersonalizationEngine instances, in-memory caching,
Contract v1.1 recommendation generation, feedback learning, concurrency safety,
and PostgreSQL persistence.
"""

import logging
import os
import threading
from typing import Any, Dict, List, Optional, Sequence

from components.personalization.adaptive import (
    AdaptivePersonalizationEngine,
    FeedbackProcessingResult,
)
from components.personalization.linucb import DEFAULT_ALPHA
from components.personalization.persistence.database import get_database_url
from components.personalization.persistence.repository import PersonalizationRepository
from components.personalization.persistence.service import (
    persist_adaptive_engine,
    restore_adaptive_engine,
)
from components.personalization.presets import MAX_IDENTIFIER_LENGTH, MOCK_ARM_PRESETS

logger = logging.getLogger(__name__)


def _validate_identifier(name: str, value: Any, max_len: int = MAX_IDENTIFIER_LENGTH) -> str:
    """Validate string identifier presence and length bound."""
    if value is None:
        raise ValueError(f"{name} cannot be None.")
    clean = str(value).strip()
    if not clean:
        raise ValueError(f"{name} cannot be empty.")
    if len(clean) > max_len:
        raise ValueError(
            f"{name} exceeds maximum supported length of {max_len} characters."
        )
    return clean


_AUTO_REPOSITORY: Any = object()


class PersonalizationRuntimeService:
    """
    FastAPI-facing runtime service managing per-user AdaptivePersonalizationEngine lifecycles.

    Key policies:
    1. Multi-User Isolation: Each user has their own isolated AdaptivePersonalizationEngine.
    2. Concurrency Safety: Per-user locks ensure simultaneous operations for the same user
       cannot mutate engine state inconsistently.
    3. Sequence & Uniqueness: Recommendation sequence values advance deterministically scoped
       per session_id (0, 1, 2, ...), ensuring unique recommendation_id generation
       (rec_<user_id>_<session_id>_<sequence>) across users, sessions, and restarts, while
       user_state.recommendation_count tracks lifetime analytics.
    4. Database Fallback / Persistence:
       - repository omitted & DATABASE_URL absent: Runs in in-memory mode without persistence attempts.
       - repository omitted & DATABASE_URL configured: Automatically connects to PostgreSQL repository.
       - explicit repository=None: Explicitly forces in-memory mode regardless of DATABASE_URL.
       - repository configured but fails: Surfaces a clear controlled error rather than
         pretending persistence succeeded.
    """

    def __init__(
        self,
        repository: Any = _AUTO_REPOSITORY,
        arms: Optional[Sequence[str]] = None,
        alpha: float = DEFAULT_ALPHA,
        min_updates_for_linucb: int = 1,
    ):
        self.arms: List[str] = list(arms) if arms is not None else list(MOCK_ARM_PRESETS)
        self.alpha: float = float(alpha)
        self.min_updates_for_linucb: int = int(min_updates_for_linucb)

        self._engines: Dict[str, AdaptivePersonalizationEngine] = {}
        self._user_locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

        # Database repository setup:
        # 1. Omitted repository (_AUTO_REPOSITORY sentinel):
        #    Auto-detect DATABASE_URL:
        #    - If DATABASE_URL is set in environment: instantiate PersonalizationRepository.
        #    - Else (DATABASE_URL absent): in-memory mode (self.repository = None).
        # 2. Explicit repository=None:
        #    Forced in-memory mode (self.repository = None), ignoring DATABASE_URL.
        # 3. Explicit repository=<repository>:
        #    Use supplied repository directly.
        if repository is _AUTO_REPOSITORY:
            if get_database_url():
                try:
                    self.repository: Optional[PersonalizationRepository] = PersonalizationRepository()
                except Exception as exc:
                    logger.error("Failed to initialize PersonalizationRepository: %s", exc)
                    raise RuntimeError(
                        f"PostgreSQL repository initialization failed for configured DATABASE_URL: {exc}"
                    ) from exc
            else:
                self.repository = None
        else:
            self.repository = repository

    def _get_user_lock(self, user_id: str) -> threading.Lock:
        """Retrieve or create a re-entrant lock specific to a user_id."""
        with self._global_lock:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = threading.Lock()
            return self._user_locks[user_id]

    def get_engine(self, user_id: str) -> AdaptivePersonalizationEngine:
        """
        Retrieve the active AdaptivePersonalizationEngine for a user.
        If not cached in memory, attempts to restore from PostgreSQL persistence.
        If no persisted record exists, creates a fresh engine for the user.
        """
        clean_user_id = _validate_identifier("user_id", user_id)

        with self._global_lock:
            if clean_user_id in self._engines:
                return self._engines[clean_user_id]

        # Engine restoration from PostgreSQL (if repository is configured)
        engine: Optional[AdaptivePersonalizationEngine] = None
        if self.repository is not None:
            try:
                engine = restore_adaptive_engine(
                    repository=self.repository,
                    user_id=clean_user_id,
                    arms=self.arms,
                    alpha=self.alpha,
                    min_updates_for_linucb=self.min_updates_for_linucb,
                )
            except Exception as exc:
                logger.error("Failed to restore engine from database for user '%s': %s", clean_user_id, exc)
                raise RuntimeError(f"Database persistence failure during restore for user '{clean_user_id}': {exc}") from exc

        # Fresh engine if user does not exist in DB
        if engine is None:
            engine = AdaptivePersonalizationEngine(
                user_id=clean_user_id,
                arms=self.arms,
                alpha=self.alpha,
                min_updates_for_linucb=self.min_updates_for_linucb,
            )
            if self.repository is not None:
                try:
                    self.repository.save_user_state(engine.user_state)
                except Exception as exc:
                    logger.error("Failed to persist initial state for user '%s': %s", clean_user_id, exc)
                    raise RuntimeError(f"Database persistence error for user '{clean_user_id}': {exc}") from exc

        with self._global_lock:
            self._engines[clean_user_id] = engine

        return engine

    def recommend(
        self,
        user_id: str,
        tier3_event: Dict[str, Any],
        sequence: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a Contract v1.1 Recommendation event for the user from a MER Tier 3 event.
        Guarantees deterministic sequence advancement and concurrency safety.
        """
        clean_user_id = _validate_identifier("user_id", user_id)
        _validate_identifier("session_id", tier3_event.get("session_id"))

        user_lock = self._get_user_lock(clean_user_id)
        with user_lock:
            engine = self.get_engine(clean_user_id)
            rec_event = engine.recommend(tier3_event, recommendation_sequence=sequence)

            # Persist updated user state and recommendation interaction
            if self.repository is not None:
                try:
                    self.repository.save_user_state(engine.user_state)
                    if engine.pending_interactions:
                        latest_interaction = engine.pending_interactions[-1]
                        self.repository.save_interaction(latest_interaction, user_id=clean_user_id)
                except Exception as exc:
                    logger.error("Database persistence failure during recommend for user '%s': %s", clean_user_id, exc)
                    raise RuntimeError(f"Database persistence error: {exc}") from exc

            return rec_event

    def process_feedback(
        self,
        user_id: str,
        feedback_event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a user feedback event, update LinUCB bandit parameters if reward applies,
        and persist changes with idempotency protections.
        Guarantees concurrency safety per user.
        """
        clean_user_id = _validate_identifier("user_id", user_id)
        if feedback_event.get("feedback_id"):
            _validate_identifier("feedback_id", feedback_event.get("feedback_id"))
        if feedback_event.get("session_id"):
            _validate_identifier("session_id", feedback_event.get("session_id"))
        if feedback_event.get("preset_id"):
            _validate_identifier("preset_id", feedback_event.get("preset_id"))

        user_lock = self._get_user_lock(clean_user_id)
        with user_lock:
            engine = self.get_engine(clean_user_id)
            result: FeedbackProcessingResult = engine.process_feedback(feedback_event)

            feedback_id = feedback_event.get("feedback_id")
            session_id = feedback_event.get("session_id")
            preset_id = feedback_event.get("preset_id")
            fb_dict = feedback_event.get("feedback", {})
            fb_type = fb_dict.get("type", "unknown")

            if self.repository is not None:
                try:
                    if result.status == "applied":
                        # 1. Persist updated LinUCB bandit state (A & b matrices)
                        self.repository.save_linucb_state(clean_user_id, engine.model)
                        # 2. Persist updated user personalization metrics
                        self.repository.save_user_state(engine.user_state)
                        # 3. Mark matched interaction feedback_applied
                        if result.recommendation_id:
                            self.repository.mark_interaction_feedback_applied(result.recommendation_id)
                        # 4. Record processed feedback ID for persistence idempotency
                        if feedback_id:
                            self.repository.save_processed_feedback(
                                {
                                    "feedback_id": feedback_id,
                                    "session_id": session_id,
                                    "preset_id": preset_id,
                                    "feedback_type": fb_type,
                                    "reward": result.reward,
                                    "raw_value": fb_dict.get("rating") or fb_dict.get("value"),
                                    "is_auxiliary": False,
                                    "recommendation_id": result.recommendation_id,
                                },
                                user_id=clean_user_id,
                            )
                    elif result.status == "auxiliary":
                        # Auxiliary feedback updates user state (e.g. view duration) but not LinUCB
                        self.repository.save_user_state(engine.user_state)
                        if feedback_id:
                            self.repository.save_processed_feedback(
                                {
                                    "feedback_id": feedback_id,
                                    "session_id": session_id,
                                    "preset_id": preset_id,
                                    "feedback_type": fb_type,
                                    "reward": None,
                                    "raw_value": fb_dict.get("duration_ms"),
                                    "is_auxiliary": True,
                                    "recommendation_id": result.recommendation_id,
                                },
                                user_id=clean_user_id,
                            )
                except Exception as exc:
                    logger.error("Database persistence failure during feedback for user '%s': %s", clean_user_id, exc)
                    raise RuntimeError(f"Database persistence error: {exc}") from exc

            return dict(result)

    def get_user_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Return a JSON-serializable dictionary representation of the user personalization state.
        Returns None if user has no in-memory or persisted state.
        """
        clean_user_id = str(user_id).strip()
        if not clean_user_id or len(clean_user_id) > MAX_IDENTIFIER_LENGTH:
            return None

        user_lock = self._get_user_lock(clean_user_id)
        with user_lock:
            with self._global_lock:
                if clean_user_id in self._engines:
                    return self._engines[clean_user_id].user_state.to_dict()

            if self.repository is not None:
                try:
                    state = self.repository.load_user_state(clean_user_id)
                    if state is not None:
                        return state.to_dict()
                except Exception as exc:
                    logger.error("Database error while loading user state for '%s': %s", clean_user_id, exc)
                    raise RuntimeError(f"Database load error: {exc}") from exc

        return None

    def clear_cache(self, user_id: Optional[str] = None) -> None:
        """
        Clear in-memory engine cache for a specific user or all users.
        Enables testing runtime reconstruction from persistence without restarting the process.
        """
        with self._global_lock:
            if user_id is not None:
                self._engines.pop(str(user_id).strip(), None)
            else:
                self._engines.clear()

    def persist_user(self, user_id: str) -> None:
        """Explicitly persist all components of an active engine to PostgreSQL."""
        clean_user_id = _validate_identifier("user_id", user_id)
        user_lock = self._get_user_lock(clean_user_id)
        with user_lock:
            with self._global_lock:
                engine = self._engines.get(clean_user_id)
            if engine and self.repository is not None:
                try:
                    persist_adaptive_engine(self.repository, engine, user_id=clean_user_id)
                except Exception as exc:
                    logger.error("Database error while persisting user '%s': %s", clean_user_id, exc)
                    raise RuntimeError(f"Database persistence error: {exc}") from exc
