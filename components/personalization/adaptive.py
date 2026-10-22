"""
In-Memory Adaptive Personalization Engine and Closed Learning Loop.

Connects MER Tier 3 events, Context Vector generation, Cold-Start/LinUCB arm selection,
Contract v1.1 Recommendation events, FeedbackEvent rewards, LinUCB model updating,
and UserPersonalizationState preferences tracking.
"""

from typing import Any, Dict, List, Optional, Sequence, Set
import numpy as np

from components.personalization.cold_start import select_cold_start_preset
from components.personalization.context import (
    CONTEXT_DIMENSION,
    ContextVector,
    build_context_vector,
)
from components.personalization.engine import build_recommendation_event
from components.personalization.feedback import RewardResult, calculate_reward
from components.personalization.linucb import DEFAULT_ALPHA, LinUCB, LinUCBSelection
from components.personalization.presets import MAX_IDENTIFIER_LENGTH, MOCK_ARM_PRESETS
from components.personalization.user_state import (
    DEFAULT_MAX_HISTORY_SIZE,
    UserPersonalizationState,
)


class FeedbackProcessingResult(dict):
    """
    Structured outcome of feedback processing and bandit model updating.
    Inherits from dict for serialization compatibility and convenient key access,
    while also providing typed attribute access.
    """

    def __init__(
        self,
        status: str,
        applied: bool,
        feedback_id: Optional[str] = None,
        preset_id: Optional[str] = None,
        session_id: Optional[str] = None,
        reward: Optional[float] = None,
        arm_updated: Optional[str] = None,
        recommendation_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        super().__init__(
            status=status,
            applied=applied,
            feedback_id=feedback_id,
            preset_id=preset_id,
            session_id=session_id,
            reward=reward,
            arm_updated=arm_updated,
            recommendation_id=recommendation_id,
            message=message or "",
        )

    @property
    def status(self) -> str:
        """Processing status: 'applied', 'auxiliary', 'duplicate', or 'unmatched'."""
        return self["status"]

    @property
    def applied(self) -> bool:
        """True if the LinUCB bandit model was updated; False otherwise."""
        return self["applied"]

    @property
    def feedback_id(self) -> Optional[str]:
        return self["feedback_id"]

    @property
    def preset_id(self) -> Optional[str]:
        return self["preset_id"]

    @property
    def session_id(self) -> Optional[str]:
        return self["session_id"]

    @property
    def reward(self) -> Optional[float]:
        return self["reward"]

    @property
    def arm_updated(self) -> Optional[str]:
        return self["arm_updated"]

    @property
    def recommendation_id(self) -> Optional[str]:
        return self["recommendation_id"]

    @property
    def message(self) -> str:
        return self["message"]


class AdaptivePersonalizationEngine:
    """
    In-memory Adaptive Personalization Engine integrating contextual bandit learning
    and structured user history/preferences tracking.

    Pipeline:
    1. Cold-Start Phase:
       When successful_update_count < min_updates_for_linucb (default 1),
       recommendations are driven by deterministic cold-start quadrant mapping
       (strategy="cold_start", score=None).
    2. Adaptive LinUCB Phase:
       Once successful_update_count >= min_updates_for_linucb, recommendations
       are driven by LinUCB arm selection (strategy="linucb", score=float).
    3. User History & Preference Tracking:
       Maintains structured UserPersonalizationState recording per-preset metrics,
       bounded histories, cumulative rewards, and preference summaries.
    4. Interaction Storage & Feedback Matching:
       Stores pending recommendation context in memory. Matches feedback events to the
       most recent unprocessed interaction matching (session_id, preset_id).
    5. Duplicate Protection:
       Tracks processed feedback_id values to prevent duplicate reward updates.
    """

    def __init__(
        self,
        arms: Optional[Sequence[str]] = None,
        context_dimension: int = CONTEXT_DIMENSION,
        alpha: float = DEFAULT_ALPHA,
        min_updates_for_linucb: int = 1,
        model: Optional[LinUCB] = None,
        user_id: Optional[str] = None,
        user_state: Optional[UserPersonalizationState] = None,
        max_history_size: int = DEFAULT_MAX_HISTORY_SIZE,
    ):
        self.context_dimension: int = int(context_dimension)
        self.alpha: float = float(alpha)
        self.min_updates_for_linucb: int = max(1, int(min_updates_for_linucb))

        if model is not None:
            self.model = model
            model_arms = list(model.arms)
            if arms is not None:
                self.arms = list(dict.fromkeys(list(arms) + model_arms))
                self.model.ensure_arms(self.arms)
            else:
                self.arms = model_arms
        else:
            self.arms = list(arms) if arms is not None else list(MOCK_ARM_PRESETS)
            self.model = LinUCB(
                arms=self.arms,
                context_dimension=self.context_dimension,
                alpha=self.alpha,
            )

        for arm in self.arms:
            if len(str(arm).strip()) > MAX_IDENTIFIER_LENGTH:
                raise ValueError(
                    f"preset_id '{arm}' exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
                )
        if user_id and len(str(user_id).strip()) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"user_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
            )

        self.successful_update_count: int = 0
        self.pending_interactions: List[Dict[str, Any]] = []
        self.processed_feedback_ids: Set[str] = set()
        self._session_sequences: Dict[str, int] = {}

        # User Personalization State
        if user_state is not None:
            self.user_state: UserPersonalizationState = user_state
        else:
            self.user_state = UserPersonalizationState(
                user_id=user_id or "user-default",
                max_history_size=max_history_size,
                presets=self.arms,
            )

    @property
    def _internal_sequence(self) -> int:
        """Fallback property returning total sequence count across active sessions."""
        return sum(self._session_sequences.values())

    @_internal_sequence.setter
    def _internal_sequence(self, val: int) -> None:
        pass

    @property
    def is_linucb_active(self) -> bool:
        """Returns True if the engine has transitioned from cold_start to linucb."""
        return self.successful_update_count >= self.min_updates_for_linucb

    def recommend(
        self,
        tier3_event: Dict[str, Any],
        recommendation_sequence: Optional[int] = None,
        candidate_visual_ids: Optional[Sequence[str]] = None,
        default_visual_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a Contract v1.1 Recommendation event from a MER Tier 3 event.

        Modes:
        1. Final Member 2 Integration Mode (when candidate_visual_ids is provided):
           - Member 2 owns emotion-to-visual mapping and supplies top-K emotion-safe candidate IDs.
           - For cold-start (successful_update_count < min_updates_for_linucb): returns Member 2's default_visual_id.
           - Once learned (successful_update_count >= min_updates_for_linucb): ranks candidate_visual_ids via LinUCB.
           - Never selects a visual outside candidate_visual_ids.
        2. Demo / Fallback Mode (when candidate_visual_ids is None):
           - Preserves existing 50% viva demo quadrant mapping to mock presets.

        Contract v1.1:
        - Output recommended_preset_id carries the selected visual/preset identifier.
        """
        session_id = str(tier3_event["session_id"]).strip()
        if len(session_id) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"session_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
            )
        audio_time_ms = tier3_event["audio_time_ms"]

        if recommendation_sequence is not None:
            seq = int(recommendation_sequence)
            self._session_sequences[session_id] = seq + 1
        else:
            seq = self._session_sequences.get(session_id, 0)
            self._session_sequences[session_id] = seq + 1

        # Candidate parameters validation and normalization
        normalized_candidates: Optional[List[str]] = None
        clean_default_visual_id: Optional[str] = None

        if candidate_visual_ids is not None:
            if len(candidate_visual_ids) == 0:
                raise ValueError("candidate_visual_ids cannot be empty.")

            seen_candidates: Set[str] = set()
            normalized_candidates = []
            for cid in candidate_visual_ids:
                if cid is None:
                    raise ValueError("candidate_visual_ids cannot contain None.")
                clean_cid = str(cid).strip()
                if not clean_cid:
                    raise ValueError("candidate_visual_ids cannot contain empty or blank strings.")
                if len(clean_cid) > MAX_IDENTIFIER_LENGTH:
                    raise ValueError(
                        f"candidate visual_id '{clean_cid}' exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
                    )
                if clean_cid not in seen_candidates:
                    seen_candidates.add(clean_cid)
                    normalized_candidates.append(clean_cid)

            if default_visual_id is None:
                raise ValueError("default_visual_id must be provided when candidate_visual_ids is specified.")
            clean_default_visual_id = str(default_visual_id).strip()
            if not clean_default_visual_id:
                raise ValueError("default_visual_id cannot be empty or whitespace-only.")
            if len(clean_default_visual_id) > MAX_IDENTIFIER_LENGTH:
                raise ValueError(
                    f"default_visual_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
                )
            if clean_default_visual_id not in seen_candidates:
                raise ValueError(
                    f"default_visual_id '{clean_default_visual_id}' must exist inside candidate_visual_ids."
                )

            # Ensure all candidates exist in LinUCB model and in self.arms
            self.model.ensure_arms(normalized_candidates)
            for arm in normalized_candidates:
                if arm not in self.arms:
                    self.arms.append(arm)
        else:
            if default_visual_id is not None:
                raise ValueError("default_visual_id cannot be specified without candidate_visual_ids.")

        # 1. Build context vector from Tier 3 continuous emotion
        ctx: ContextVector = build_context_vector(tier3_event)

        # 2. Decide selection policy based on learning state & integration mode
        preset_id: str
        strategy: str
        score: Optional[float]

        if candidate_visual_ids is not None:
            # Final Member 2 Integration Mode:
            if not self.is_linucb_active:
                # Cold-start policy: Member 2 default candidate
                if clean_default_visual_id is None:
                    raise ValueError("default_visual_id must be provided when candidate_visual_ids is specified.")
                preset_id = clean_default_visual_id
                strategy = "cold_start"
                score = None
            else:
                # LinUCB ranking strictly within candidate_visual_ids
                if normalized_candidates is None:
                    raise ValueError("candidate_visual_ids cannot be empty.")
                selection: LinUCBSelection = self.model.select_arm(ctx, eligible_arms=normalized_candidates)
                preset_id = selection.selected_arm
                strategy = "linucb"
                score = float(selection.selected_score)
        else:
            # Demo / Fallback Mode (Member 2 candidates not supplied):
            if not self.is_linucb_active:
                valence = float(tier3_event["emotion"]["valence"])
                arousal = float(tier3_event["emotion"]["arousal"])
                preset_id = select_cold_start_preset(valence, arousal)
                strategy = "cold_start"
                score = None
            else:
                selection = self.model.select_arm(ctx)
                preset_id = selection.selected_arm
                strategy = "linucb"
                score = float(selection.selected_score)


        # 3. Build Contract v1.1 Recommendation event
        rec_event = build_recommendation_event(
            session_id=session_id,
            sequence=seq,
            audio_time_ms=audio_time_ms,
            recommended_preset_id=preset_id,
            strategy=strategy,
            score=score,
            user_id=self.user_state.user_id if self.user_state else None,
        )

        # 4. Store pending interaction context in memory
        interaction = {
            "session_id": session_id,
            "sequence": seq,
            "recommendation_id": rec_event["recommendation_id"],
            "recommended_preset_id": preset_id,
            "context_vector": ctx.to_list(),
            "audio_time_ms": audio_time_ms,
            "strategy": strategy,
            "score": score,
            "feedback_applied": False,
        }
        if normalized_candidates is not None:
            interaction["candidate_visual_ids"] = list(normalized_candidates)
        self.pending_interactions.append(interaction)

        # 5. Record to user personalization state
        if self.user_state is not None:
            self.user_state.record_recommendation(
                preset_id=preset_id,
                recommendation_id=rec_event["recommendation_id"],
                session_id=session_id,
                audio_time_ms=audio_time_ms,
                strategy=strategy,
                score=score,
                sequence=seq,
            )

        return rec_event

    def process_feedback(
        self,
        feedback_event: Dict[str, Any],
        strict: bool = False,
    ) -> FeedbackProcessingResult:
        """
        Process a user feedback event and update the LinUCB model if applicable.

        1. Rejects duplicate feedback IDs from updating the model or user state.
        2. Calculates the scalar reward via calculate_reward().
        3. Matches the most recent unprocessed pending interaction for (session_id, preset_id).
        4. If reward is None (e.g. view_duration): records auxiliary telemetry in user state
           without updating the LinUCB model.
        5. If reward is numerical: updates the LinUCB model, marks interaction as processed,
           increments successful_update_count, and updates user state metrics.
        """
        raw_feedback_id = feedback_event.get("feedback_id")
        raw_session_id = feedback_event.get("session_id")
        raw_preset_id = feedback_event.get("preset_id")

        feedback_id: Optional[str] = str(raw_feedback_id).strip() if raw_feedback_id is not None else None
        session_id: str = str(raw_session_id).strip() if raw_session_id is not None else ""
        preset_id: str = str(raw_preset_id).strip() if raw_preset_id is not None else ""

        if feedback_id and len(feedback_id) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"feedback_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
            )
        if len(session_id) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"session_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
            )
        if len(preset_id) > MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"preset_id exceeds maximum supported length of {MAX_IDENTIFIER_LENGTH} characters."
            )


        # 1. Duplicate feedback ID check
        if feedback_id and feedback_id in self.processed_feedback_ids:
            if strict:
                raise ValueError(f"Duplicate feedback_id '{feedback_id}' has already been processed.")
            return FeedbackProcessingResult(
                status="duplicate",
                applied=False,
                feedback_id=feedback_id,
                preset_id=preset_id,
                session_id=session_id,
                message=f"Duplicate feedback_id '{feedback_id}' ignored.",
            )

        # 2. Reward calculation
        reward_result: RewardResult = calculate_reward(feedback_event)

        # 3. Matching policy: find the most recent unprocessed pending interaction
        matching_interaction: Optional[Dict[str, Any]] = None
        for interaction in reversed(self.pending_interactions):
            if (
                not interaction["feedback_applied"]
                and interaction["session_id"] == session_id
                and interaction["recommended_preset_id"] == preset_id
            ):
                matching_interaction = interaction
                break

        # 4. Handle unmatched interaction
        if matching_interaction is None:
            if strict:
                raise KeyError(
                    f"No pending unprocessed recommendation found for session_id '{session_id}' "
                    f"and preset_id '{preset_id}'."
                )
            return FeedbackProcessingResult(
                status="unmatched",
                applied=False,
                feedback_id=feedback_id,
                preset_id=preset_id,
                session_id=session_id,
                reward=reward_result.reward,
                message=(
                    f"No pending unprocessed recommendation found for session_id '{session_id}' "
                    f"and preset_id '{preset_id}'."
                ),
            )

        # Record feedback_id as processed
        if feedback_id:
            self.processed_feedback_ids.add(feedback_id)

        # 5. Auxiliary feedback handling (reward is None, e.g. view_duration)
        if reward_result.reward is None:
            if self.user_state is not None:
                self.user_state.record_feedback(
                    feedback_type=reward_result.feedback_type,
                    preset_id=preset_id,
                    session_id=session_id,
                    reward=None,
                    feedback_id=feedback_id,
                    recommendation_id=matching_interaction["recommendation_id"],
                    raw_value=reward_result.raw_value,
                    is_auxiliary=True,
                )
            return FeedbackProcessingResult(
                status="auxiliary",
                applied=False,
                feedback_id=feedback_id,
                preset_id=preset_id,
                session_id=session_id,
                reward=None,
                recommendation_id=matching_interaction["recommendation_id"],
                message="Auxiliary feedback recorded; no bandit update performed.",
            )

        # 6. Apply scalar reward update to LinUCB
        self.model.update(
            arm_id=preset_id,
            context_vector=matching_interaction["context_vector"],
            reward=reward_result.reward,
        )

        # 7. Mark interaction as rewarded
        matching_interaction["feedback_applied"] = True

        # 8. Increment successful update counter
        self.successful_update_count += 1

        # 9. Record to user personalization state
        if self.user_state is not None:
            self.user_state.record_feedback(
                feedback_type=reward_result.feedback_type,
                preset_id=preset_id,
                session_id=session_id,
                reward=reward_result.reward,
                feedback_id=feedback_id,
                recommendation_id=matching_interaction["recommendation_id"],
                raw_value=reward_result.raw_value,
                is_auxiliary=False,
            )

        return FeedbackProcessingResult(
            status="applied",
            applied=True,
            feedback_id=feedback_id,
            preset_id=preset_id,
            session_id=session_id,
            reward=reward_result.reward,
            arm_updated=preset_id,
            recommendation_id=matching_interaction["recommendation_id"],
            message=f"LinUCB model updated successfully for arm '{preset_id}'.",
        )
