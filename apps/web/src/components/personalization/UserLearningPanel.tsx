import React from "react";
import type { UserPersonalizationStateData } from "../../types/personalization";
import { PRESET_REGISTRY } from "../../types/personalization";

interface UserLearningPanelProps {
  userState: UserPersonalizationStateData | null;
  userId: string;
  isLoading: boolean;
  onRefresh: () => void;
}

export const UserLearningPanel: React.FC<UserLearningPanelProps> = ({
  userState,
  userId,
  isLoading,
  onRefresh,
}) => {
  const summary = userState?.preference_summary;
  const preferredPresetId = summary?.most_positively_rewarded_preset;
  const preferredPresetMeta = preferredPresetId ? PRESET_REGISTRY[preferredPresetId] : null;

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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
            User Analytics & LinUCB Learning State
          </h3>
          <p style={{ margin: "0.2rem 0 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
            State queried live from PostgreSQL persistence for <code>{userId}</code>
          </p>
        </div>

        <button
          id="btn-refresh-user-state"
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.4rem 0.85rem",
            borderRadius: "0.375rem",
            backgroundColor: isLoading ? "rgba(56, 189, 248, 0.2)" : "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(56, 189, 248, 0.35)",
            color: "#38bdf8",
            fontSize: "0.78rem",
            fontWeight: 600,
            cursor: isLoading ? "not-allowed" : "pointer",
            transition: "all 0.15s ease",
            boxShadow: "0 2px 6px rgba(0, 0, 0, 0.3)",
          }}
        >
          {isLoading ? (
            <>
              <span
                style={{
                  display: "inline-block",
                  width: "10px",
                  height: "10px",
                  border: "2px solid #38bdf8",
                  borderTopColor: "transparent",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              <span>Querying PostgreSQL...</span>
            </>
          ) : (
            <>
              <span>↻</span>
              <span>Refresh State</span>
            </>
          )}
        </button>
      </div>

      {userState ? (
        <>
          {/* Key Metrics Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
              gap: "0.75rem",
            }}
          >
            {/* Learning Updates */}
            <div
              style={{
                backgroundColor: "rgba(15, 23, 42, 0.75)",
                padding: "0.85rem 1rem",
                borderRadius: "0.5rem",
                border: "1px solid rgba(168, 85, 247, 0.25)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#c084fc", fontWeight: 600 }}>
                Learning Updates
              </div>
              <div
                style={{
                  fontSize: "1.6rem",
                  fontWeight: 800,
                  color: "#f8fafc",
                  fontFamily: "monospace",
                  marginTop: "0.2rem",
                }}
              >
                {userState.successful_learning_updates}
              </div>
              <div style={{ fontSize: "0.68rem", color: "#94a3b8", marginTop: "0.2rem" }}>
                {userState.successful_learning_updates >= 1 ? "LinUCB Active" : "Cold Start Phase"}
              </div>
            </div>

            {/* Average Reward */}
            <div
              style={{
                backgroundColor: "rgba(15, 23, 42, 0.75)",
                padding: "0.85rem 1rem",
                borderRadius: "0.5rem",
                border: "1px solid rgba(16, 185, 129, 0.25)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#34d399", fontWeight: 600 }}>
                Average Reward
              </div>
              <div
                style={{
                  fontSize: "1.6rem",
                  fontWeight: 800,
                  fontFamily: "monospace",
                  color:
                    userState.average_reward !== null
                      ? userState.average_reward > 0
                        ? "#34d399"
                        : userState.average_reward < 0
                        ? "#f87171"
                        : "#f8fafc"
                      : "#64748b",
                  marginTop: "0.2rem",
                }}
              >
                {userState.average_reward !== null
                  ? `${userState.average_reward > 0 ? "+" : ""}${userState.average_reward.toFixed(2)}`
                  : "0.00"}
              </div>
              <div style={{ fontSize: "0.68rem", color: "#94a3b8", marginTop: "0.2rem" }}>
                Over {userState.numerical_reward_count} evaluations
              </div>
            </div>

            {/* Recommendations Generated */}
            <div
              style={{
                backgroundColor: "rgba(15, 23, 42, 0.75)",
                padding: "0.85rem 1rem",
                borderRadius: "0.5rem",
                border: "1px solid rgba(56, 189, 248, 0.25)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: 600 }}>
                Recommendations
              </div>
              <div
                style={{
                  fontSize: "1.6rem",
                  fontWeight: 800,
                  color: "#f8fafc",
                  fontFamily: "monospace",
                  marginTop: "0.2rem",
                }}
              >
                {userState.recommendation_count}
              </div>
              <div style={{ fontSize: "0.68rem", color: "#94a3b8", marginTop: "0.2rem" }}>
                Lifetime generated
              </div>
            </div>

            {/* Feedback Events */}
            <div
              style={{
                backgroundColor: "rgba(15, 23, 42, 0.75)",
                padding: "0.85rem 1rem",
                borderRadius: "0.5rem",
                border: "1px solid rgba(245, 158, 11, 0.25)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#fbbf24", fontWeight: 600 }}>
                Feedback Events
              </div>
              <div
                style={{
                  fontSize: "1.6rem",
                  fontWeight: 800,
                  color: "#f8fafc",
                  fontFamily: "monospace",
                  marginTop: "0.2rem",
                }}
              >
                {userState.feedback_count}
              </div>
              <div style={{ fontSize: "0.68rem", color: "#94a3b8", marginTop: "0.2rem" }}>
                Total interactions
              </div>
            </div>
          </div>

          {/* Preferred Preset Callout */}
          <div
            style={{
              padding: "0.75rem 1rem",
              borderRadius: "0.5rem",
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.5rem",
            }}
          >
            <div>
              <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                Current Most Positively Rewarded Preset:
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.2rem" }}>
                {preferredPresetMeta ? (
                  <>
                    <span
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        backgroundColor: preferredPresetMeta.accentColor,
                        boxShadow: `0 0 8px ${preferredPresetMeta.accentColor}`,
                      }}
                    />
                    <span style={{ fontWeight: 700, color: "#f8fafc", fontSize: "0.95rem" }}>
                      {preferredPresetMeta.name}
                    </span>
                    <code style={{ fontSize: "0.75rem", color: "#38bdf8" }}>
                      {preferredPresetMeta.id}
                    </code>
                  </>
                ) : (
                  <span style={{ color: "#64748b", fontSize: "0.85rem" }}>
                    No clear positive preference established yet (requires positive feedback).
                  </span>
                )}
              </div>
            </div>

            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
              Last Recommended:{" "}
              <code style={{ color: "#cbd5e1" }}>
                {userState.last_recommended_preset || "none"}
              </code>
            </div>
          </div>

          {/* Arm Stats Breakdown Table */}
          {userState.preset_stats && (
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#94a3b8", marginBottom: "0.4rem" }}>
                Bandit Arm Interaction Breakdown:
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "0.5rem",
                }}
              >
                {Object.values(userState.preset_stats).map((stat) => {
                  const meta = PRESET_REGISTRY[stat.preset_id];
                  return (
                    <div
                      key={stat.preset_id}
                      style={{
                        padding: "0.6rem 0.8rem",
                        borderRadius: "0.4rem",
                        backgroundColor: "rgba(15, 23, 42, 0.45)",
                        border: "1px solid rgba(255, 255, 255, 0.05)",
                        fontSize: "0.78rem",
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 700,
                          color: meta?.accentColor || "#cbd5e1",
                          display: "flex",
                          justifyContent: "space-between",
                        }}
                      >
                        <span>{meta?.name || stat.preset_id}</span>
                        <span style={{ fontFamily: "monospace" }}>
                          Recs: {stat.recommendation_count}
                        </span>
                      </div>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          color: "#94a3b8",
                          marginTop: "0.25rem",
                          fontSize: "0.72rem",
                        }}
                      >
                        <span>👍 {stat.like_count} | 👎 {stat.dislike_count}</span>
                        <span
                          style={{
                            fontFamily: "monospace",
                            color:
                              stat.cumulative_reward > 0
                                ? "#34d399"
                                : stat.cumulative_reward < 0
                                ? "#f87171"
                                : "#94a3b8",
                          }}
                        >
                          Rew: {stat.cumulative_reward > 0 ? "+" : ""}
                          {stat.cumulative_reward.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      ) : (
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            borderRadius: "0.5rem",
            padding: "1.25rem",
            textAlign: "center",
            color: "#64748b",
            fontSize: "0.85rem",
          }}
        >
          No interaction history found for <code>{userId}</code>. Submit recommendations and feedback to observe real LinUCB learning.
        </div>
      )}
    </div>
  );
};
