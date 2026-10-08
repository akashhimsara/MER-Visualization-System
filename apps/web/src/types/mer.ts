export interface MERTier3Emotion {
    valence: number;
    arousal: number;
    confidence: number | null;
}

export interface MERTier3Event {
    schema_version: "1.1";
    event_type: "mer.tier3";
    session_id: string;
    sequence: number;
    audio_time_ms: number;
    emotion: MERTier3Emotion;
}
