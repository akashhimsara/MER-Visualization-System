import React, { useState } from "react";
import type { RecommendationResponse, FeedbackResponse } from "../../types/personalization";

interface TechnicalDetailsPanelProps {
  valence: number;
  arousal: number;
  recommendation: RecommendationResponse | null;
  lastFeedback: FeedbackResponse | null;
  userId: string;
  candidates?: string[];
  defaultVisualId?: string;
}

export const TechnicalDetailsPanel: React.FC<TechnicalDetailsPanelProps> = ({
  valence,
  arousal,
  recommendation,
  lastFeedback,
  userId,
  candidates = [],
  defaultVisualId,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const contextVectorStr = `[${valence.toFixed(2)}, ${arousal.toFixed(2)}, 1.00]`;

  return (
    <div
      style={{
        backgroundColor: "rgba(15, 23, 42, 0.6)",
        borderRadius: "0.75rem",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        overflow: "hidden",
        transition: "all 0.2s ease",
      }}
    >
      {/* Accordion Toggle Header */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: "100%",
          padding: "0.85rem 1.25rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "transparent",
          border: "none",
          color: "#cbd5e1",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "1rem" }}>🔬</span>
          <span style={{ fontWeight: 700, fontSize: "0.9rem" }}>
            Technical Architecture & Candidate-Aware LinUCB Formulation
          </span>
          <span
            style={{
              fontSize: "0.7rem",
              color: "#94a3b8",
              backgroundColor: "rgba(255, 255, 255, 0.06)",
              padding: "0.15rem 0.4rem",
              borderRadius: "0.25rem",
            }}
          >
            Technical Architecture Reference
          </span>
        </div>
        <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
          {isOpen ? "▲ Collapse" : "▼ Expand (Technical Architecture Q&A)"}
        </span>
      </button>


      {/* Collapsible Content */}
      {isOpen && (
        <div
          style={{
            padding: "0 1.25rem 1.25rem 1.25rem",
            borderTop: "1px solid rgba(255, 255, 255, 0.06)",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
            fontSize: "0.82rem",
            color: "#94a3b8",
          }}
        >
          {/* Card 1: Context Vector & Decision Rule */}
          <div
            style={{
              backgroundColor: "rgba(9, 13, 22, 0.6)",
              padding: "0.85rem 1rem",
              borderRadius: "0.5rem",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <div style={{ fontWeight: 700, color: "#38bdf8", marginBottom: "0.4rem" }}>
              1. Context Vector Representation
            </div>
            <p style={{ margin: "0 0 0.5rem 0", lineHeight: 1.4 }}>
              Current vector representation <code style={{ color: "#f8fafc" }}>x_t ∈ ℝ³</code> passed to LinUCB:
            </p>
            <div
              style={{
                fontFamily: "monospace",
                color: "#f59e0b",
                backgroundColor: "rgba(0, 0, 0, 0.3)",
                padding: "0.4rem 0.6rem",
                borderRadius: "0.3rem",
                fontSize: "0.85rem",
              }}
            >
              x_t = {contextVectorStr}
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "0.4rem" }}>
              Dimension 0: Valence | Dimension 1: Arousal | Dimension 2: Constant Bias (1.0)
            </div>
            <div style={{ marginTop: "0.6rem", fontSize: "0.75rem", color: "#cbd5e1" }}>
              <strong>Candidate Source:</strong> Simulated Member 2 compatibility output
              <br />
              <strong>Eligible LinUCB Arms:</strong>{" "}
              <code style={{ color: "#38bdf8" }}>{candidates.length > 0 ? candidates.join(", ") : "All arms"}</code>
              <br />
              <strong>Cold Start:</strong> Member 2 <code>default_visual_id</code> ({defaultVisualId || "fallback"})
              <br />
              <strong>Learned Mode:</strong> Disjoint LinUCB ranking strictly within eligible candidates
            </div>
          </div>

          {/* Card 2: LinUCB Mathematical Formulation */}
          <div
            style={{
              backgroundColor: "rgba(9, 13, 22, 0.6)",
              padding: "0.85rem 1rem",
              borderRadius: "0.5rem",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <div style={{ fontWeight: 700, color: "#a855f7", marginBottom: "0.4rem" }}>
              2. Disjoint LinUCB Mathematical Engine
            </div>
            <p style={{ margin: "0 0 0.4rem 0", lineHeight: 1.4 }}>
              For each visual arm <code style={{ color: "#f8fafc" }}>a ∈ Candidates</code>, ridge regression matrices are updated:
            </p>
            <div
              style={{
                fontFamily: "monospace",
                color: "#c084fc",
                backgroundColor: "rgba(0, 0, 0, 0.3)",
                padding: "0.35rem 0.5rem",
                borderRadius: "0.3rem",
                fontSize: "0.78rem",
              }}
            >
              A_a ← A_a + x_t x_tᵀ (initialized to I₃)
              <br />
              b_a ← b_a + r_t x_t
              <br />
              θ̂_a = A_a⁻¹ b_a
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "0.4rem" }}>
              Decision Rule: a* = argmax_{'{a ∈ Candidates}'} [ θ̂_aᵀ x_t + α √(x_tᵀ A_a⁻¹ x_t) ] (α = 0.50)
            </div>
            <div style={{ marginTop: "0.5rem", fontSize: "0.72rem", color: "#94a3b8" }}>
              <strong>Feedback Types:</strong> Explicit ratings/likes and behavioral dwell time supported by backend.
            </div>
          </div>

          {/* Card 3: Responsibility Boundary */}
          <div
            style={{
              backgroundColor: "rgba(9, 13, 22, 0.6)",
              padding: "0.85rem 1rem",
              borderRadius: "0.5rem",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <div style={{ fontWeight: 700, color: "#10b981", marginBottom: "0.4rem" }}>
              3. Component Boundaries & Ownership
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", fontSize: "0.78rem" }}>
              <div>
                <strong>Emotion-to-Visual Mapping:</strong> <span style={{ color: "#38bdf8" }}>Member 2 responsibility</span>
              </div>
              <div>
                <strong>User Preference Ranking:</strong> <span style={{ color: "#a855f7" }}>Member 4 responsibility</span>
              </div>
              <div
                style={{
                  backgroundColor: "rgba(56, 189, 248, 0.08)",
                  padding: "0.4rem 0.6rem",
                  borderRadius: "0.3rem",
                  border: "1px solid rgba(56, 189, 248, 0.2)",
                  color: "#e2e8f0",
                  fontStyle: "italic",
                  fontSize: "0.75rem",
                  marginTop: "0.2rem",
                }}
              >
                "Member 4 does not generate emotion-to-visual mappings in final integration."
              </div>
              <div style={{ marginTop: "0.2rem" }}>
                <strong>Active User:</strong> <code>{userId}</code> | <strong>Persistence:</strong> PostgreSQL
              </div>
              {recommendation && (
                <div>
                  <strong>Active Choice:</strong>{" "}
                  <code style={{ color: "#38bdf8" }}>{recommendation.recommended_preset_id}</code>{" "}
                  ({recommendation.strategy === "linucb" ? "LinUCB Selected" : "Member 2 Cold Start Default"})
                </div>
              )}
              {lastFeedback && (
                <div>
                  <strong>Last Processed Reward:</strong>{" "}
                  <code style={{ color: "#34d399" }}>
                    {typeof lastFeedback.reward === "number"
                      ? `${lastFeedback.reward > 0 ? "+" : ""}${lastFeedback.reward.toFixed(2)}`
                      : "None"}
                  </code>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
