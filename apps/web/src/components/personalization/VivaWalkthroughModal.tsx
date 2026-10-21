import React from "react";

interface VivaWalkthroughModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const VivaWalkthroughModal: React.FC<VivaWalkthroughModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  const steps = [
    {
      title: "Step 1 — Establish Baseline Preference for User A",
      items: [
        "Select User A (demo-user-a) from the profile selector at the top.",
        "Click the quick emotion preset 'High Positive / High Arousal' (Valence: 0.80, Arousal: 0.75).",
        "Click 'Get Recommendation' — notice the Strategy is 'Cold Start' (heuristic default).",
        "Click 'Like (+1.0 Reward)' to submit positive feedback.",
        "Click 'Get Recommendation' again — notice the Strategy has automatically switched to 'LinUCB Bandit (Learned)' with a positive UCB score!",
        "Click 'Like' once more to solidify User A's affinity for Energetic Positive.",
      ],
    },
    {
      title: "Step 2 — Introduce Divergent Feedback for User B",
      items: [
        "Switch to User B (demo-user-b) using the profile switcher.",
        "Notice User B starts with 0 learning updates (clean isolated bandit state).",
        "Keep the exact same emotion context: Valence = 0.80, Arousal = 0.75.",
        "Click 'Get Recommendation' — User B receives the initial cold-start default.",
        "Now click 'Dislike (-1.0 Reward)' — User B explicitly rejects this preset!",
        "Click 'Get Recommendation' again — LinUCB penalizes the disliked arm and explores an alternative preset (e.g. Calm Positive or Tense Negative)!",
        "Click 'Like' on the alternative preset for User B.",
      ],
    },
    {
      title: "Step 3 — Viva Proof: Personalization Divergence",
      items: [
        "Look at the 'Personalization Divergence' comparison card.",
        "Click 'Compare Users' to refresh both states from PostgreSQL.",
        "Highlight the divergence badge:",
        "Explain to the panel: When both users have learned distinct preferences, the badge shows 'PREFERENCE DIVERGENCE LEARNED'. When both users receive differing recommendations under the exact same emotion context (e.g. V=0.80, A=0.75), the badge confirms 'RECOMMENDATION DIVERGENCE PROVEN'!",
      ],
    },
  ];

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "#0f172a",
          borderRadius: "0.85rem",
          border: "1px solid rgba(56, 189, 248, 0.4)",
          maxWidth: "680px",
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "1.75rem",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
          color: "#e2e8f0",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.25rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "1.3rem" }}>🎓</span>
              <h2 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 800, color: "#f8fafc" }}>
                Viva / Presentation Demo Script
              </h2>
            </div>
            <p style={{ margin: "0.3rem 0 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
              Standard 3-step demonstration sequence showing cold-start transition and multi-user divergence.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: "rgba(255, 255, 255, 0.08)",
              border: "none",
              color: "#94a3b8",
              fontSize: "1.2rem",
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {steps.map((s, idx) => (
            <div
              key={s.title}
              style={{
                backgroundColor: "rgba(30, 41, 59, 0.6)",
                borderRadius: "0.6rem",
                padding: "1rem",
                border: "1px solid rgba(255, 255, 255, 0.08)",
              }}
            >
              <div
                style={{
                  fontSize: "0.95rem",
                  fontWeight: 700,
                  color: idx === 0 ? "#f59e0b" : idx === 1 ? "#10b981" : "#38bdf8",
                  marginBottom: "0.6rem",
                }}
              >
                {s.title}
              </div>
              <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.83rem", color: "#cbd5e1", lineHeight: 1.6 }}>
                {s.items.map((it, i) => (
                  <li key={i} style={{ marginBottom: "0.25rem" }}>
                    {it}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div style={{ marginTop: "1.5rem", textAlign: "right" }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: "0.6rem 1.4rem",
              borderRadius: "0.5rem",
              backgroundColor: "#0284c7",
              color: "#ffffff",
              border: "none",
              fontWeight: 700,
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            Got it, Let's Demo
          </button>
        </div>
      </div>
    </div>
  );
};
