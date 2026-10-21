import React, { useState } from "react";
import type { RecommendationResponse, FeedbackResponse } from "../../types/personalization";

interface TechnicalDetailsPanelProps {
  valence: number;
  arousal: number;
  recommendation: RecommendationResponse | null;
  lastFeedback: FeedbackResponse | null;
  userId: string;
}

export const TechnicalDetailsPanel: React.FC<TechnicalDetailsPanelProps> = ({
  valence,
  arousal,
  recommendation,
  lastFeedback,
  userId,
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
            Technical Architecture & LinUCB Formulation
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
            Viva Defense Reference
          </span>
        </div>
        <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
          {isOpen ? "▲ Collapse" : "▼ Expand (For Viva Technical Q&A)"}
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
              For each visual arm <code style={{ color: "#f8fafc" }}>a</code>, ridge regression matrices are updated:
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
              Decision Rule: a* = argmax [ θ̂_aᵀ x_t + α √(x_tᵀ A_a⁻¹ x_t) ] with α = 0.50
            </div>
          </div>

          {/* Card 3: Active State & Identity Boundary */}
          <div
            style={{
              backgroundColor: "rgba(9, 13, 22, 0.6)",
              padding: "0.85rem 1rem",
              borderRadius: "0.5rem",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <div style={{ fontWeight: 700, color: "#10b981", marginBottom: "0.4rem" }}>
              3. Runtime & Identity Scope
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: "0.78rem" }}>
              <div>
                <strong>Active User:</strong> <code>{userId}</code>
              </div>
              <div>
                <strong>Persistence Layer:</strong> PostgreSQL (Alembic <code>0001_personalization</code>)
              </div>
              <div>
                <strong>Recommendation ID format:</strong> Fixed 36-char deterministic UUID5
              </div>
              <div>
                <strong>Identity Boundary:</strong> Caller-supplied <code>user_id</code> (Strict 128-char limit; JWT authentication scheduled for upcoming auth milestone).
              </div>
              {recommendation && (
                <div>
                  <strong>Active Inference:</strong>{" "}
                  <code style={{ color: "#38bdf8" }}>{recommendation.recommended_preset_id}</code>{" "}
                  (Strategy: <strong style={{ color: recommendation.strategy === "linucb" ? "#c084fc" : "#34d399" }}>{recommendation.strategy}</strong>
                  {recommendation.score !== null ? `, UCB Score: ${recommendation.score.toFixed(4)}` : ""})
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
