import React from "react";
import type { RecommendationResponse } from "../../types/personalization";
import { PRESET_REGISTRY } from "../../types/personalization";

interface RecommendationCardProps {
  recommendation: RecommendationResponse | null;
  isLoading: boolean;
  onGetRecommendation: () => void;
  valence: number;
  arousal: number;
  disabled?: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  isLoading,
  onGetRecommendation,
  valence,
  arousal,
  disabled = false,
}) => {
  const presetMeta = recommendation
    ? PRESET_REGISTRY[recommendation.recommended_preset_id]
    : null;

  return (
    <div
      style={{
        backgroundColor: "rgba(30, 41, 59, 0.7)",
        borderRadius: "0.75rem",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        padding: "1.25rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* Title & Primary Action Button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
            Personalized Preset Recommendation
          </h3>
          <p style={{ margin: "0.2rem 0 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
            Real-time inference using Context Vector <code>[{valence.toFixed(2)}, {arousal.toFixed(2)}, 1.0]</code>
          </p>
        </div>

        <button
          type="button"
          disabled={isLoading || disabled}
          onClick={onGetRecommendation}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.6rem 1.25rem",
            borderRadius: "0.5rem",
            background: isLoading
              ? "rgba(56, 189, 248, 0.3)"
              : "linear-gradient(135deg, #0284c7, #38bdf8)",
            border: "1px solid rgba(56, 189, 248, 0.6)",
            color: "#ffffff",
            fontSize: "0.9rem",
            fontWeight: 700,
            cursor: isLoading || disabled ? "not-allowed" : "pointer",
            boxShadow: "0 4px 14px rgba(2, 132, 199, 0.4)",
            transition: "all 0.2s ease",
          }}
        >
          {isLoading ? (
            <>
              <span
                style={{
                  display: "inline-block",
                  width: "14px",
                  height: "14px",
                  border: "2px solid #ffffff",
                  borderTopColor: "transparent",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              <span>Inferencing...</span>
            </>
          ) : (
            <>
              <span>⚡</span>
              <span>Get Recommendation</span>
            </>
          )}
        </button>
      </div>

      {/* Recommendation Details Body */}
      {recommendation ? (
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.75)",
            borderRadius: "0.6rem",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "1rem",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
          }}
        >
          {/* Preset Info */}
          <div>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase" }}>
              Recommended Visual Arm
            </span>
            <div style={{ marginTop: "0.25rem" }}>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc" }}>
                {presetMeta ? presetMeta.name : recommendation.recommended_preset_id}
              </div>
              <code
                style={{
                  fontSize: "0.75rem",
                  color: "#38bdf8",
                  backgroundColor: "rgba(56, 189, 248, 0.1)",
                  padding: "0.15rem 0.4rem",
                  borderRadius: "0.25rem",
                }}
              >
                {recommendation.recommended_preset_id}
              </code>
            </div>
          </div>

          {/* Decision Strategy */}
          <div>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase" }}>
              Active Decision Strategy
            </span>
            <div style={{ marginTop: "0.35rem" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  padding: "0.35rem 0.75rem",
                  borderRadius: "0.4rem",
                  fontSize: "0.85rem",
                  fontWeight: 700,
                  backgroundColor:
                    recommendation.strategy === "linucb"
                      ? "rgba(168, 85, 247, 0.2)"
                      : "rgba(16, 185, 129, 0.2)",
                  color:
                    recommendation.strategy === "linucb" ? "#c084fc" : "#34d399",
                  border: `1px solid ${
                    recommendation.strategy === "linucb"
                      ? "rgba(168, 85, 247, 0.45)"
                      : "rgba(16, 185, 129, 0.45)"
                  }`,
                }}
              >
                <span>{recommendation.strategy === "linucb" ? "🧠" : "❄️"}</span>
                <span>
                  {recommendation.strategy === "linucb"
                    ? "LinUCB Bandit (Learned)"
                    : "Cold-Start Heuristic"}
                </span>
              </span>
            </div>
          </div>

          {/* UCB Score & Sequence */}
          <div>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase" }}>
              Score / Confidence
            </span>
            <div style={{ marginTop: "0.25rem", fontSize: "0.95rem", fontWeight: 600 }}>
              {recommendation.score !== null ? (
                <span style={{ color: "#a855f7", fontFamily: "monospace" }}>
                  UCB = {recommendation.score.toFixed(4)}
                </span>
              ) : (
                <span style={{ color: "#64748b" }}>None (Cold-Start Rule)</span>
              )}
            </div>
            <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>
              Event Sequence: #{recommendation.sequence}
            </div>
          </div>

          {/* Recommendation Identifier */}
          <div>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase" }}>
              Recommendation ID (UUID5)
            </span>
            <div
              style={{
                marginTop: "0.25rem",
                fontFamily: "monospace",
                fontSize: "0.75rem",
                color: "#cbd5e1",
                wordBreak: "break-all",
              }}
            >
              {recommendation.recommendation_id}
            </div>
          </div>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            borderRadius: "0.6rem",
            border: "1px dashed rgba(255, 255, 255, 0.12)",
            padding: "1.5rem",
            textAlign: "center",
            color: "#64748b",
            fontSize: "0.9rem",
          }}
        >
          No recommendation requested yet for this session. Adjust the emotion sliders above and click{" "}
          <strong style={{ color: "#38bdf8" }}>"Get Recommendation"</strong> to test cold-start or LinUCB.
        </div>
      )}
    </div>
  );
};
