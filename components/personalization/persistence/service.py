"""
Service and Factory Functions for Personalization Restoration and Persistence.

Decouples AdaptivePersonalizationEngine from direct database models,
providing clean save and restore workflows.
"""

from typing import Optional, Sequence
from components.personalization.adaptive import AdaptivePersonalizationEngine
from components.personalization.linucb import DEFAULT_ALPHA, LinUCB
from components.personalization.persistence.repository import PersonalizationRepository
from components.personalization.presets import MOCK_ARM_PRESETS
from components.personalization.user_state import UserPersonalizationState


def restore_adaptive_engine(
    repository: PersonalizationRepository,
    user_id: str,
    arms: Optional[Sequence[str]] = None,
    context_dimension: int = 3,
    alpha: float = DEFAULT_ALPHA,
    min_updates_for_linucb: int = 1,
) -> Optional[AdaptivePersonalizationEngine]:
    """
    Restore an AdaptivePersonalizationEngine instance from PostgreSQL persistence.

    Flow:
    1. Load persisted UserPersonalizationState. If None, return None.
    2. Load persisted LinUCB parameters. If None, instantiate a default LinUCB model.
    3. Load pending interactions and processed feedback IDs.
    4. Construct and configure AdaptivePersonalizationEngine.
    """
    user_state = repository.load_user_state(user_id)
    if user_state is None:
        return None

    model = repository.load_linucb_state(
        user_id=user_id,
        expected_dimension=context_dimension,
        fallback_alpha=alpha,
    )
    if model is None:
        model = LinUCB(
            arms=arms or list(MOCK_ARM_PRESETS),
            context_dimension=context_dimension,
            alpha=alpha,
        )

    pending = repository.load_pending_interactions(user_id)
    seen_fb_ids = repository.load_processed_feedback_ids(user_id)

    engine = AdaptivePersonalizationEngine(
        arms=arms,
        context_dimension=context_dimension,
        alpha=alpha,
        min_updates_for_linucb=min_updates_for_linucb,
        model=model,
        user_state=user_state,
    )

    engine.successful_update_count = user_state.successful_learning_updates
    engine.pending_interactions = pending
    engine.processed_feedback_ids = seen_fb_ids

    return engine


def persist_adaptive_engine(
    repository: PersonalizationRepository,
    engine: AdaptivePersonalizationEngine,
    user_id: Optional[str] = None,
) -> None:
    """
    Persist an AdaptivePersonalizationEngine's full state (user metrics and LinUCB matrices).
    """
    uid = user_id or engine.user_state.user_id

    # 1. Save user personalization state
    repository.save_user_state(engine.user_state)

    # 2. Save LinUCB model matrices
    repository.save_linucb_state(uid, engine.model)

    # 3. Save any pending interactions
    for interaction in engine.pending_interactions:
        repository.save_interaction(interaction, uid)
