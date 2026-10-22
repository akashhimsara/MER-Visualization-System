import React, { useState, useEffect } from "react";
import type { FeedbackResponse, FeedbackType } from "../../types/personalization";

interface FeedbackControlsProps {
  hasActiveRecommendation: boolean;
  recommendedPresetId: string | null;
  onSubmitFeedback: (type: FeedbackType, rating?: number) => Promise<FeedbackResponse>;
  isSubmitting: boolean;
  lastFeedbackResponse: FeedbackResponse | null;
  feedbackSubmittedForCurrentRec: boolean;
  disabled?: boolean;
}

export const FeedbackControls: React.FC<FeedbackControlsProps> = ({
  hasActiveRecommendation,
  recommendedPresetId,
  onSubmitFeedback,
  isSubmitting,
  lastFeedbackResponse,
  feedbackSubmittedForCurrentRec,
  disabled = false,
}) => {
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [submittedRating, setSubmittedRating] = useState<number | null>(null);

  // Clear submitted rating if recommendation resets or changes
  useEffect(() => {
    if (!feedbackSubmittedForCurrentRec) {
      setSubmittedRating(null);
    }
  }, [feedbackSubmittedForCurrentRec, recommendedPresetId]);

  const canSubmit =
    hasActiveRecommendation &&
    !isSubmitting &&
    !feedbackSubmittedForCurrentRec &&
    !disabled;

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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
            User Feedback & Bandit Learning
          </h3>
          <p style={{ margin: "0.2rem 0 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
            Submits a reward to update Disjoint LinUCB matrices <code>(A_a, b_a)</code> for preset arm{" "}
            <code style={{ color: "#38bdf8" }}>{recommendedPresetId || "none"}</code>.
          </p>
        </div>

        {feedbackSubmittedForCurrentRec && (
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              padding: "0.25rem 0.65rem",
              borderRadius: "0.375rem",
              backgroundColor: "rgba(16, 185, 129, 0.2)",
              color: "#34d399",
              border: "1px solid rgba(16, 185, 129, 0.4)",
            }}
          >
            ✓ Feedback Recorded for Current Preset
          </span>
        )}
      </div>

      {/* Buttons Row: Like, Dislike, Star Rating */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
          alignItems: "center",
          opacity: canSubmit ? 1 : 0.65,
        }}
      >
        {/* Like Button */}
        <button
          type="button"
          disabled={!canSubmit}
          onClick={() => onSubmitFeedback("like")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.6rem 1.25rem",
            borderRadius: "0.5rem",
            backgroundColor: "rgba(16, 185, 129, 0.18)",
            border: "1.5px solid rgba(16, 185, 129, 0.5)",
            color: "#34d399",
            fontWeight: 700,
            fontSize: "0.9rem",
            cursor: canSubmit ? "pointer" : "not-allowed",
            transition: "all 0.15s ease",
            boxShadow: canSubmit ? "0 2px 8px rgba(16, 185, 129, 0.25)" : "none",
          }}
        >
          <span style={{ fontSize: "1.1rem" }}>👍</span>
          <span>Like (+1.0 Reward)</span>
        </button>

        {/* Dislike Button */}
        <button
          type="button"
          disabled={!canSubmit}
          onClick={() => onSubmitFeedback("dislike")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.6rem 1.25rem",
            borderRadius: "0.5rem",
            backgroundColor: "rgba(244, 63, 94, 0.18)",
            border: "1.5px solid rgba(244, 63, 94, 0.5)",
            color: "#f87171",
            fontWeight: 700,
            fontSize: "0.9rem",
            cursor: canSubmit ? "pointer" : "not-allowed",
            transition: "all 0.15s ease",
            boxShadow: canSubmit ? "0 2px 8px rgba(244, 63, 94, 0.25)" : "none",
          }}
        >
          <span style={{ fontSize: "1.1rem" }}>👎</span>
          <span>Dislike (-1.0 Reward)</span>
        </button>

        {/* 1-5 Star Ratings */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.4rem 0.8rem",
            borderRadius: "0.5rem",
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <span style={{ fontSize: "0.8rem", color: "#94a3b8", marginRight: "0.25rem" }}>
            Rating:
          </span>
          {[1, 2, 3, 4, 5].map((star) => {
            const isFilled =
              hoverRating !== null
                ? star <= hoverRating
                : submittedRating !== null && star <= submittedRating;
            return (
              <button
                key={star}
                id={`btn-rate-${star}`}
                type="button"
                disabled={!canSubmit}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(null)}
                onClick={() => {
                  setSubmittedRating(star);
                  onSubmitFeedback("rating", star);
                }}
                title={`Rate ${star} / 5 (${((star - 3) / 2 > 0 ? "+" : "") + ((star - 3) / 2).toFixed(1)} reward)`}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "1.2rem",
                  cursor: canSubmit ? "pointer" : "default",
                  color: isFilled ? "#fbbf24" : "#64748b",
                  padding: "0 0.1rem",
                  transition: "color 0.15s ease, transform 0.1s ease",
                  transform: hoverRating !== null && star <= hoverRating ? "scale(1.2)" : "scale(1)",
                }}
              >
                ★
              </button>
            );
          })}
          {submittedRating !== null && (
            <span style={{ fontSize: "0.75rem", color: "#fbbf24", fontWeight: 700, marginLeft: "0.3rem" }}>
              ({submittedRating}/5 ★)
            </span>
          )}
        </div>
      </div>


      {/* Outcome Status / Response Card */}
      {lastFeedbackResponse && (
        <div
          style={{
            padding: "0.85rem 1rem",
            borderRadius: "0.5rem",
            backgroundColor:
              lastFeedbackResponse.applied
                ? "rgba(16, 185, 129, 0.12)"
                : lastFeedbackResponse.status === "duplicate"
                ? "rgba(245, 158, 11, 0.12)"
                : "rgba(59, 130, 246, 0.12)",
            border: `1px solid ${
              lastFeedbackResponse.applied
                ? "rgba(16, 185, 129, 0.35)"
                : lastFeedbackResponse.status === "duplicate"
                ? "rgba(245, 158, 11, 0.35)"
                : "rgba(59, 130, 246, 0.35)"
            }`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "0.5rem",
            animation: "fadeIn 0.3s ease",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <span style={{ fontSize: "1.1rem" }}>
              {lastFeedbackResponse.applied
                ? "✅"
                : lastFeedbackResponse.status === "duplicate"
                ? "⚠️"
                : "ℹ️"}
            </span>
            <div>
              <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f8fafc" }}>
                {lastFeedbackResponse.message}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                Status:{" "}
                <strong style={{ color: "#ffffff", textTransform: "uppercase" }}>
                  {lastFeedbackResponse.status}
                </strong>
                {lastFeedbackResponse.arm_updated && (
                  <span>
                    {" "}
                    | Updated Arm: <code>{lastFeedbackResponse.arm_updated}</code>
                  </span>
                )}
              </div>
            </div>
          </div>

          {lastFeedbackResponse.reward !== null &&
            lastFeedbackResponse.reward !== undefined && (
              <div
                style={{
                  fontSize: "1.1rem",
                  fontWeight: 800,
                  fontFamily: "monospace",
                  color:
                    lastFeedbackResponse.reward > 0
                      ? "#34d399"
                      : lastFeedbackResponse.reward < 0
                      ? "#f87171"
                      : "#94a3b8",
                  backgroundColor: "rgba(0, 0, 0, 0.3)",
                  padding: "0.3rem 0.7rem",
                  borderRadius: "0.4rem",
                }}
              >
                Reward: {lastFeedbackResponse.reward > 0 ? "+" : ""}
                {lastFeedbackResponse.reward.toFixed(2)}
              </div>
            )}
        </div>
      )}
    </div>
  );
};
