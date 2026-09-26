from src.pipeline.smoothing import EmotionSmoother
from src.pipeline.temporal_analysis import TemporalAnalyzer
from src.pipeline.change_detection import MeaningfulChangeDetector
from src.pipeline.candidate_gen import TransitionCandidateGenerator
from src.pipeline.scoring import TransitionScorer
from src.pipeline.continuity import ContinuityController


class TransitionOrchestrator:

    def __init__(self):

        self.smoother = EmotionSmoother(window_size=3)

        self.temporal_analyzer = TemporalAnalyzer()

        self.change_detector = MeaningfulChangeDetector(
            confidence_threshold=0.70
        )

        self.candidate_generator = TransitionCandidateGenerator()

        self.scorer = TransitionScorer()

        self.continuity_controller = ContinuityController(
            cooldown_seconds=5.0
        )

        self.previous_emotion = None

    def process_frame(
        self,
        timestamp,
        emotion,
        confidence,
        beat=False,
        downbeat=False,
        onset=False,
        energy_change=False
    ):

        # 1. Add emotion to smoother
        self.smoother.add(emotion, confidence)

        # 2. Get smoothed emotion
        smoothed_emotion = self.smoother.get_smoothed_emotion()

       # 3. Add data to temporal analyzer
        self.temporal_analyzer.add(
            timestamp,
            smoothed_emotion,
            confidence
        )

        # Calculate persistence
        persistence = self.temporal_analyzer.calculate_persistence(
            smoothed_emotion
        )
        
        # 4. Detect meaningful emotion change
        emotion_changed = False

        if self.previous_emotion is not None:

            emotion_changed = self.change_detector.is_meaningful(
                self.previous_emotion,
                smoothed_emotion,
                confidence
            )

        # 5. Generate transition candidate
        candidate = self.candidate_generator.is_candidate(
            beat=beat,
            downbeat=downbeat,
            onset=onset,
            energy_change=energy_change
        )

        # 6. Calculate transition score
        score = self.scorer.calculate_score(
            emotion_change=emotion_changed,
            confidence=confidence,
            persistence=persistence,
            beat=beat,
            downbeat=downbeat,
            onset=onset,
            energy_change=energy_change
        )
        # 7. Check cooldown
        can_transition = self.continuity_controller.can_transition(
            timestamp
        )

        # 8. Final transition decision
        transition = (
            candidate
            and score >= 0.50
            and can_transition
        )

        # 9. Record transition time
        if transition:
            self.continuity_controller.record_transition(timestamp)

        # 10. Update previous emotion
        self.previous_emotion = smoothed_emotion

        return {
            "timestamp": timestamp,
            "emotion": smoothed_emotion,
            "emotion_changed": emotion_changed,
            "candidate": candidate,
            "score": score,
            "can_transition": can_transition,
            "transition": transition,
            "persistence": persistence,
        }