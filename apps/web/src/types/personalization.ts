/**
 * TypeScript types for Member 4: Adaptive Personalization & User Analytics
 * Contract v1.1 compliant interfaces.
 */

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

export interface RecommendationResponse {
  schema_version: "1.1";
  event_type: "personalization.recommendation";
  session_id: string;
  sequence: number;
  audio_time_ms: number;
  recommendation_id: string;
  recommended_preset_id: string;
  score: number | null;
  strategy: "default" | "cold_start" | "linucb";
}

export type FeedbackType = "like" | "dislike" | "rating" | "preset_select" | "preset_skip" | "view_duration";

export interface FeedbackData {
  type: FeedbackType;
  rating?: number | null;
  duration_ms?: number | null;
}

export interface FeedbackEvent {
  schema_version: "1.1";
  event_type: "feedback.event";
  session_id: string;
  sequence: number;
  audio_time_ms: number;
  feedback_id: string;
  preset_id: string;
  feedback: FeedbackData;
}

export interface FeedbackResponse {
  status: "applied" | "auxiliary" | "duplicate" | "unmatched";
  applied: boolean;
  feedback_id?: string | null;
  preset_id?: string | null;
  session_id?: string | null;
  reward?: number | null;
  arm_updated?: string | null;
  recommendation_id?: string | null;
  message: string;
}

export interface PresetStatsData {
  preset_id: string;
  recommendation_count: number;
  feedback_count: number;
  like_count: number;
  dislike_count: number;
  rating_count: number;
  rating_sum: number;
  preset_select_count: number;
  preset_skip_count: number;
  cumulative_reward: number;
  numerical_reward_count: number;
  average_reward: number | null;
  view_duration_count: number;
  total_duration_ms: number;
}

export interface PreferenceSummaryData {
  user_id: string;
  recommendation_count: number;
  feedback_count: number;
  successful_learning_updates: number;
  average_observed_reward: number | null;
  most_positively_rewarded_preset: string | null;
  most_frequently_selected_preset: string | null;
  most_frequently_liked_preset: string | null;
  is_beyond_cold_start: boolean;
}

export interface UserPersonalizationStateData {
  user_id: string;
  max_history_size: number;
  recommendation_count: number;
  feedback_count: number;
  successful_learning_updates: number;
  last_recommended_preset: string | null;
  last_feedback_type: string | null;
  cumulative_reward: number;
  numerical_reward_count: number;
  average_reward: number | null;
  preference_summary: PreferenceSummaryData;
  preset_stats: Record<string, PresetStatsData>;
  recent_recommendations: Array<Record<string, unknown>>;
  recent_feedback: Array<Record<string, unknown>>;
}

export interface PresetMetadata {
  id: string;
  name: string;
  description: string;
  accentColor: string;
  secondaryColor: string;
  moodQuadrant: string;
}

export type EmotionCategory = "HAPPY" | "ENERGETIC" | "CALM" | "SAD";

export interface SimulatedMember2Output {
  emotionCategory: EmotionCategory;
  candidateVisualIds: string[];
  defaultVisualId: string;
}

export const MEMBER2_COMPATIBILITY_TABLE: Record<
  EmotionCategory,
  { candidates: string[]; defaultVisualId: string }
> = {
  CALM: {
    candidates: ["COSMIC_IRIS", "PARTICLE_AURORA", "COSMIC_BLOOM"],
    defaultVisualId: "COSMIC_IRIS",
  },
  HAPPY: {
    candidates: ["COSMIC_BLOOM", "PARTICLE_AURORA", "NEON_MANDALA"],
    defaultVisualId: "COSMIC_BLOOM",
  },
  ENERGETIC: {
    candidates: ["NEON_MANDALA", "PARTICLE_AURORA"],
    defaultVisualId: "NEON_MANDALA",
  },
  SAD: {
    candidates: ["COSMIC_IRIS", "COSMIC_BLOOM", "PARTICLE_AURORA"],
    defaultVisualId: "COSMIC_IRIS",
  },
};

export function getSimulatedMember2Output(valence: number, arousal: number): SimulatedMember2Output {
  let category: EmotionCategory;
  if (valence >= 0) {
    if (arousal >= 0.55) {
      category = "ENERGETIC";
    } else if (arousal >= -0.25) {
      category = "HAPPY";
    } else {
      category = "CALM";
    }
  } else {
    if (arousal >= 0.2) {
      category = "CALM";
    } else {
      category = "SAD";
    }
  }

  const entry = MEMBER2_COMPATIBILITY_TABLE[category] || MEMBER2_COMPATIBILITY_TABLE.HAPPY;
  return {
    emotionCategory: category,
    candidateVisualIds: [...entry.candidates],
    defaultVisualId: entry.defaultVisualId,
  };
}

export const PRESET_REGISTRY: Record<string, PresetMetadata> = {
  // Official Member 2 Current Machine Visual IDs
  COSMIC_BLOOM: {
    id: "COSMIC_BLOOM",
    name: "Cosmic Bloom",
    description: "Radiant blooming petals with warm magenta and golden pulses, evoking vibrant harmony and organic beauty.",
    accentColor: "#ec4899",
    secondaryColor: "#f59e0b",
    moodQuadrant: "High Valence, Moderate Arousal (Happy / Radiant)",
  },
  PARTICLE_AURORA: {
    id: "PARTICLE_AURORA",
    name: "Particle Aurora",
    description: "Harmonic undulating wave ribbons with gentle emerald and cyan atmospheric glow and drifting stardust.",
    accentColor: "#10b981",
    secondaryColor: "#06b6d4",
    moodQuadrant: "Positive Valence, Low/Moderate Arousal (Calm / Ethereal)",
  },
  NEON_MANDALA: {
    id: "NEON_MANDALA",
    name: "Neon Mandala",
    description: "High-energy intricate geometric sacred symmetry, rotating laser spokes, and rapid kinetic radial pulses.",
    accentColor: "#a855f7",
    secondaryColor: "#38bdf8",
    moodQuadrant: "High Arousal, Positive Valence (Energetic / Euphoric)",
  },
  COSMIC_IRIS: {
    id: "COSMIC_IRIS",
    name: "Cosmic Iris / Void Portal",
    description: "Deep cosmic portal with dark indigo and violet accretion disk, slow celestial gravitational drift.",
    accentColor: "#6366f1",
    secondaryColor: "#1e1b4b",
    moodQuadrant: "Low Arousal, Contemplative (Calm / Subdued)",
  },

  // Backward-compatible fallback mock presets
  "mock-energetic-positive": {
    id: "mock-energetic-positive",
    name: "Energetic Positive Flow (Fallback)",
    description: "High energy, vibrant warm particles with dynamic radial pulses and rapid kinetic flow.",
    accentColor: "#f59e0b",
    secondaryColor: "#ec4899",
    moodQuadrant: "High Arousal, Positive Valence",
  },
  "mock-calm-positive": {
    id: "mock-calm-positive",
    name: "Calm Positive Aurora (Fallback)",
    description: "Smooth undulating harmonic waves with gentle emerald and cyan atmospheric glow.",
    accentColor: "#10b981",
    secondaryColor: "#06b6d4",
    moodQuadrant: "Low Arousal, Positive Valence",
  },
  "mock-tense-negative": {
    id: "mock-tense-negative",
    name: "Tense Negative Geometry (Fallback)",
    description: "Sharp angular polygon shifts, chromatic aberration, and erratic high-frequency vibrations.",
    accentColor: "#f43f5e",
    secondaryColor: "#8b5cf6",
    moodQuadrant: "High Arousal, Negative Valence",
  },
  "mock-calm-negative": {
    id: "mock-calm-negative",
    name: "Calm Negative Deep Drift (Fallback)",
    description: "Slow-moving deep navy and indigo mist with contemplative, sparse particle dissipation.",
    accentColor: "#6366f1",
    secondaryColor: "#334155",
    moodQuadrant: "Low Arousal, Negative Valence",
  },
};
