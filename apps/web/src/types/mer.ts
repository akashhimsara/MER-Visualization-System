export interface MEROnset {
  detected: boolean;
  strength: number | null;
}

export interface MERBeat {
  detected: boolean;
  strength: number | null;
}

export interface MERTier1Event {
  schema_version: "1.1";
  event_type: "mer.tier1";
  session_id: string;
  sequence: number;
  audio_time_ms: number;
  rms: number;
  spectral_centroid_hz: number;
  onset: MEROnset;
  beat?: MERBeat | null;
}

export interface MERTier2Event {
  schema_version: "1.1";
  event_type: "mer.tier2";
  session_id: string;
  sequence: number;
  audio_time_ms: number;
  tempo_bpm: number;
  tempo_confidence: number | null;
}

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

export type MEREvent = MERTier1Event | MERTier2Event | MERTier3Event;
