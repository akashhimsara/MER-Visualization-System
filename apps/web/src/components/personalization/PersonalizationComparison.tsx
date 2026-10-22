import React from "react";
import type { UserPersonalizationStateData } from "../../types/personalization";
import { PRESET_REGISTRY } from "../../types/personalization";

export interface UserRecommendationSnapshot {
  recommended_preset_id: string;
  valence: number;
  arousal: number;
  strategy?: string;
  candidates?: string[];
  default_visual_id?: string;
}

interface PersonalizationComparisonProps {
  stateA: UserPersonalizationStateData | null;
  stateB: UserPersonalizationStateData | null;
  recA?: UserRecommendationSnapshot | null;
  recB?: UserRecommendationSnapshot | null;
  onRefreshBoth: () => void;
  isLoading: boolean;
}

export const PersonalizationComparison: React.FC<PersonalizationComparisonProps> = ({
  stateA,
  stateB,
  recA,
  recB,
  onRefreshBoth,
  isLoading,
}) => {
  const prefA = stateA?.preference_summary?.most_positively_rewarded_preset;
  const prefB = stateB?.preference_summary?.most_positively_rewarded_preset;

  const metaA = prefA ? PRESET_REGISTRY[prefA] : null;
  const metaB = prefB ? PRESET_REGISTRY[prefB] : null;

  // Normalize candidate set for deterministic membership comparison
  const normalizeCandidates = (c?: string[]) =>
    c ? [...c].sort().join(",") : "";

  // 1. Same emotion context tolerance check (|Δ| < 0.05)
  const isSameEmotionContext = Boolean(
    recA &&
    recB &&
    Math.abs(recA.valence - recB.valence) < 0.05 &&
    Math.abs(recA.arousal - recB.arousal) < 0.05
  );

  // 2. Same candidate set verification
  const isSameCandidates = Boolean(
    recA &&
    recB &&
    recA.candidates &&
    recB.candidates &&
    recA.candidates.length > 0 &&
    normalizeCandidates(recA.candidates) === normalizeCandidates(recB.candidates)
  );

  // 3. Different recommended preset check
  const isDifferentRecommendation = Boolean(
    recA &&
    recB &&
    recA.recommended_preset_id &&
    recB.recommended_preset_id &&
    recA.recommended_preset_id !== recB.recommended_preset_id
  );

  // Strongest proof: ALL 3 conditions satisfied
  const hasRecommendationDivergence = Boolean(
    isSameEmotionContext && isSameCandidates && isDifferentRecommendation
  );

  // Weaker label: Historical preference divergence learned
  const hasPreferenceDivergence = Boolean(
    !hasRecommendationDivergence &&
    stateA &&
    stateB &&
    prefA &&
    prefB &&
    prefA !== prefB
  );

  // Dynamic badge styling
  let badgeLabel = "LIVE COMPARISON";
  let badgeColor = "#38bdf8";
  let badgeBg = "rgba(56, 189, 248, 0.15)";
  let badgeBorder = "rgba(56, 189, 248, 0.3)";

  if (hasRecommendationDivergence) {
    badgeLabel = "PERSONALIZED RECOMMENDATION DIVERGENCE PROVEN";
    badgeColor = "#34d399";
    badgeBg = "rgba(16, 185, 129, 0.2)";
    badgeBorder = "rgba(16, 185, 129, 0.4)";
  } else if (hasPreferenceDivergence) {
    badgeLabel = "PREFERENCE DIVERGENCE LEARNED";
    badgeColor = "#c084fc";
    badgeBg = "rgba(168, 85, 247, 0.2)";
    badgeBorder = "rgba(168, 85, 247, 0.4)";
  }

  return (
    <div
      style={{
        backgroundColor: "rgba(30, 41, 59, 0.7)",
        borderRadius: "0.75rem",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
              Personalization Divergence (Interactive Demonstration)
            </h3>
            <span
              style={{
                fontSize: "0.7rem",
                fontWeight: 700,
                padding: "0.2rem 0.55rem",
                borderRadius: "0.375rem",
                backgroundColor: badgeBg,
                color: badgeColor,
                border: `1px solid ${badgeBorder}`,
                letterSpacing: "0.02em",
              }}
            >
              {badgeLabel}
            </span>
          </div>
          <p style={{ margin: "0.2rem 0 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
            {hasRecommendationDivergence
              ? `Proven: Same emotion context (V: ${recA?.valence.toFixed(2)}, A: ${recA?.arousal.toFixed(2)}) & identical Member 2 candidates produce divergent recommendations: "${recA?.recommended_preset_id}" for User A vs "${recB?.recommended_preset_id}" for User B.`
              : hasPreferenceDivergence
              ? `Learned: User A preferred preset is "${prefA}" while User B is "${prefB}". Evaluate both users under identical candidate set to prove recommendation divergence.`
              : "Proves that identical emotion context and candidate spaces produce divergent recommendations based on learned user preferences."}
          </p>
        </div>

        <button
          type="button"
          onClick={onRefreshBoth}
          disabled={isLoading}
          style={{
            padding: "0.35rem 0.75rem",
            borderRadius: "0.375rem",
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            color: "#94a3b8",
            fontSize: "0.78rem",
            cursor: isLoading ? "not-allowed" : "pointer",
            transition: "all 0.15s ease",
          }}
        >
          {isLoading ? "Querying..." : "↻ Compare Users"}
        </button>
      </div>

      {/* Shared Context Verification Criteria Bar */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "0.75rem",
          padding: "0.75rem 1rem",
          backgroundColor: "rgba(15, 23, 42, 0.8)",
          borderRadius: "0.5rem",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          fontSize: "0.78rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ color: "#94a3b8" }}>1. Same Emotion Context:</span>
          <span
            style={{
              fontWeight: 700,
              padding: "0.15rem 0.5rem",
              borderRadius: "0.25rem",
              backgroundColor: isSameEmotionContext ? "rgba(16, 185, 129, 0.2)" : "rgba(100, 116, 139, 0.15)",
              color: isSameEmotionContext ? "#34d399" : "#64748b",
            }}
          >
            {isSameEmotionContext ? "YES" : "NO"}
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ color: "#94a3b8" }}>2. Same Member 2 Candidates:</span>
          <span
            style={{
              fontWeight: 700,
              padding: "0.15rem 0.5rem",
              borderRadius: "0.25rem",
              backgroundColor: isSameCandidates ? "rgba(16, 185, 129, 0.2)" : "rgba(100, 116, 139, 0.15)",
              color: isSameCandidates ? "#34d399" : "#64748b",
            }}
          >
            {isSameCandidates ? "YES" : "NO"}
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ color: "#94a3b8" }}>3. Different Recommendation:</span>
          <span
            style={{
              fontWeight: 700,
              padding: "0.15rem 0.5rem",
              borderRadius: "0.25rem",
              backgroundColor: isDifferentRecommendation ? "rgba(16, 185, 129, 0.2)" : "rgba(100, 116, 139, 0.15)",
              color: isDifferentRecommendation ? "#34d399" : "#64748b",
            }}
          >
            {isDifferentRecommendation ? "YES" : "NO"}
          </span>
        </div>
      </div>

      {/* Side-by-Side Dual User Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* User A Card */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.75)",
            borderRadius: "0.6rem",
            border: "1.5px solid rgba(245, 158, 11, 0.35)",
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span
                style={{
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  backgroundColor: "#f59e0b",
                  boxShadow: "0 0 8px #f59e0b",
                }}
              />
              <span style={{ fontWeight: 800, fontSize: "1rem", color: "#f8fafc" }}>User A</span>
              <code style={{ fontSize: "0.7rem", color: "#94a3b8" }}>demo-integration-user-a</code>
            </div>
            <span
              style={{
                fontSize: "0.7rem",
                color: "#f59e0b",
                fontWeight: 600,
                backgroundColor: "rgba(245, 158, 11, 0.1)",
                padding: "0.15rem 0.4rem",
                borderRadius: "0.25rem",
              }}
            >
              {stateA?.preference_summary?.is_beyond_cold_start
                ? "LinUCB Active"
                : "Cold Start"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.85rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Current Emotion V/A:</span>
              <span style={{ fontFamily: "monospace", color: "#38bdf8" }}>
                {recA ? `V: ${recA.valence.toFixed(2)}, A: ${recA.arousal.toFixed(2)}` : "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Member 2 Candidates:</span>
              <span style={{ fontSize: "0.75rem", color: "#cbd5e1" }}>
                {recA?.candidates && recA.candidates.length > 0
                  ? recA.candidates.join(", ")
                  : "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Selected Visual:</span>
              <span style={{ fontWeight: 700, color: "#f59e0b" }}>
                {recA?.recommended_preset_id || "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Strategy:</span>
              <span style={{ fontSize: "0.75rem", color: recA?.strategy === "linucb" ? "#c084fc" : "#34d399" }}>
                {recA?.strategy === "linucb" ? "LinUCB Bandit" : recA?.strategy === "cold_start" ? "Cold Start" : "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Preferred Preset:</span>
              <span style={{ fontWeight: 700, color: metaA?.accentColor || "#cbd5e1" }}>
                {metaA ? metaA.name : prefA || "Pending feedback"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Learning Updates:</span>
              <span style={{ fontFamily: "monospace", fontWeight: 700 }}>
                {stateA?.successful_learning_updates ?? 0}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Average Reward:</span>
              <span
                style={{
                  fontFamily: "monospace",
                  fontWeight: 700,
                  color:
                    (stateA?.average_reward ?? 0) > 0
                      ? "#34d399"
                      : (stateA?.average_reward ?? 0) < 0
                      ? "#f87171"
                      : "#cbd5e1",
                }}
              >
                {stateA?.average_reward !== null && stateA?.average_reward !== undefined
                  ? `${stateA.average_reward > 0 ? "+" : ""}${stateA.average_reward.toFixed(2)}`
                  : "0.00"}
              </span>
            </div>
          </div>
        </div>

        {/* User B Card */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.75)",
            borderRadius: "0.6rem",
            border: "1.5px solid rgba(16, 185, 129, 0.35)",
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span
                style={{
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  backgroundColor: "#10b981",
                  boxShadow: "0 0 8px #10b981",
                }}
              />
              <span style={{ fontWeight: 800, fontSize: "1rem", color: "#f8fafc" }}>User B</span>
              <code style={{ fontSize: "0.7rem", color: "#94a3b8" }}>demo-integration-user-b</code>
            </div>
            <span
              style={{
                fontSize: "0.7rem",
                color: "#10b981",
                fontWeight: 600,
                backgroundColor: "rgba(16, 185, 129, 0.1)",
                padding: "0.15rem 0.4rem",
                borderRadius: "0.25rem",
              }}
            >
              {stateB?.preference_summary?.is_beyond_cold_start
                ? "LinUCB Active"
                : "Cold Start"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.85rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Current Emotion V/A:</span>
              <span style={{ fontFamily: "monospace", color: "#38bdf8" }}>
                {recB ? `V: ${recB.valence.toFixed(2)}, A: ${recB.arousal.toFixed(2)}` : "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Member 2 Candidates:</span>
              <span style={{ fontSize: "0.75rem", color: "#cbd5e1" }}>
                {recB?.candidates && recB.candidates.length > 0
                  ? recB.candidates.join(", ")
                  : "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Selected Visual:</span>
              <span style={{ fontWeight: 700, color: "#10b981" }}>
                {recB?.recommended_preset_id || "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Strategy:</span>
              <span style={{ fontSize: "0.75rem", color: recB?.strategy === "linucb" ? "#c084fc" : "#34d399" }}>
                {recB?.strategy === "linucb" ? "LinUCB Bandit" : recB?.strategy === "cold_start" ? "Cold Start" : "None"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Preferred Preset:</span>
              <span style={{ fontWeight: 700, color: metaB?.accentColor || "#cbd5e1" }}>
                {metaB ? metaB.name : prefB || "Pending feedback"}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Learning Updates:</span>
              <span style={{ fontFamily: "monospace", fontWeight: 700 }}>
                {stateB?.successful_learning_updates ?? 0}
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Average Reward:</span>
              <span
                style={{
                  fontFamily: "monospace",
                  fontWeight: 700,
                  color:
                    (stateB?.average_reward ?? 0) > 0
                      ? "#34d399"
                      : (stateB?.average_reward ?? 0) < 0
                      ? "#f87171"
                      : "#cbd5e1",
                }}
              >
                {stateB?.average_reward !== null && stateB?.average_reward !== undefined
                  ? `${stateB.average_reward > 0 ? "+" : ""}${stateB.average_reward.toFixed(2)}`
                  : "0.00"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Viva Core Conclusion Banner */}
      <div
        style={{
          padding: "0.85rem 1rem",
          borderRadius: "0.5rem",
          backgroundColor: hasRecommendationDivergence
            ? "rgba(16, 185, 129, 0.12)"
            : hasPreferenceDivergence
            ? "rgba(168, 85, 247, 0.12)"
            : "rgba(15, 23, 42, 0.5)",
          border: `1px solid ${
            hasRecommendationDivergence
              ? "rgba(16, 185, 129, 0.35)"
              : hasPreferenceDivergence
              ? "rgba(168, 85, 247, 0.35)"
              : "rgba(255, 255, 255, 0.08)"
          }`,
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <span style={{ fontSize: "1.3rem" }}>
          {hasRecommendationDivergence ? "🎯" : hasPreferenceDivergence ? "📊" : "ℹ️"}
        </span>
        <div style={{ fontSize: "0.82rem", color: "#cbd5e1", lineHeight: 1.4 }}>
          {hasRecommendationDivergence ? (
            <>
              <strong style={{ color: "#34d399" }}>Personalized Recommendation Divergence Proven:</strong> Under
              identical simulated emotion context (Valence: {recA?.valence.toFixed(2)}, Arousal: {recA?.arousal.toFixed(2)})
              and identical Member 2 candidates ({recA?.candidates?.join(", ")}),
              backend recommended <code style={{ color: "#f59e0b" }}>{recA?.recommended_preset_id}</code> for{" "}
              <strong>User A</strong> vs <code style={{ color: "#10b981" }}>{recB?.recommended_preset_id}</code> for{" "}
              <strong>User B</strong> based on distinct LinUCB exploration/exploitation models.
            </>
          ) : hasPreferenceDivergence ? (
            <>
              <strong style={{ color: "#c084fc" }}>Preference Divergence Learned:</strong> <strong>User A</strong>'s
              most positively rewarded preset is <code style={{ color: "#f59e0b" }}>{prefA}</code>, while{" "}
              <strong>User B</strong>'s is <code style={{ color: "#10b981" }}>{prefB}</code>. Request recommendations
              for both users under the same emotion and candidate set to prove recommendation divergence.
            </>
          ) : (
            <>
              <strong>Evaluation Tip:</strong> Keep the same emotion context (e.g. Happy V=+0.70, A=+0.40) and candidate set.
              Provide positive feedback to User A, then switch to User B and provide positive feedback to a different candidate.
              Request recommendations again to prove personalization divergence.
            </>
          )}
        </div>
      </div>
    </div>
  );
};
