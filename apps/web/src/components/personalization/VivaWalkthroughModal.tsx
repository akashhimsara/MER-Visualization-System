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
      title: "Step 1 — Understand Architectural Boundaries & Context",
      items: [
        "Explain that Valence/Arousal (V/A) sliders represent SIMULATED Member 1 MER output.",
        "Set the demo context to HAPPY (click the 'Happy / Radiant' button: Valence = +0.70, Arousal = +0.40).",
        "Point to the 'SIMULATED MEMBER 2 OUTPUT' card: Member 2 evaluates the emotion and outputs 3 compatible candidates: COSMIC_BLOOM, PARTICLE_AURORA, NEON_MANDALA with default COSMIC_BLOOM.",
        "Emphasize the core thesis: 'Member 2 determines what visuals are emotionally compatible; Member 4 determines which among those compatible visuals is best for this specific user.'",
      ],
    },
    {
      title: "Step 2 — User A Cold Start & Preference Learning",
      items: [
        "Select User A (demo-integration-user-a) from the profile selector at the top.",
        "Click 'Get Recommendation' — initially observe Member 2's default visual (COSMIC_BLOOM) returned under the Cold Start strategy.",
        "Provide positive feedback: click 'Like (+1.0 Reward)' to train User A's LinUCB model.",
        "Click 'Get Recommendation' again — strategy now activates 'LinUCB Bandit' with a live UCB score.",
        "Click 'Like' once more to solidify User A's strong affinity for COSMIC_BLOOM.",
      ],
    },
    {
      title: "Step 3 — User B Under Identical Emotion Context & Candidate Set",
      items: [
        "Switch to User B (demo-integration-user-b). User B starts with clean, isolated state.",
        "CRITICAL: Keep the EXACT same emotion (V = +0.70, A = +0.40) and identical Member 2 candidate set.",
        "Click 'Get Recommendation' for User B — cold start initially suggests COSMIC_BLOOM.",
        "Click 'Dislike (-1.0 Reward)' — User B rejects COSMIC_BLOOM!",
        "Click 'Get Recommendation' again — LinUCB penalizes COSMIC_BLOOM and selects an alternative candidate (e.g. NEON_MANDALA or PARTICLE_AURORA) within the Member 2 candidate set.",
        "Click 'Like' on the newly recommended candidate for User B to establish their preference.",
      ],
    },
    {
      title: "Step 4 — Core Proof: Personalized Recommendation Divergence",
      items: [
        "Inspect the 'Personalization Divergence' card and click '↻ Compare Users' to query PostgreSQL.",
        "Verify all 3 criteria are satisfied: 1. Same Emotion Context = YES, 2. Same Member 2 Candidates = YES, 3. Different Recommendation = YES.",
        "Confirm the badge shows 'PERSONALIZED RECOMMENDATION DIVERGENCE PROVEN'!",
        "Explain to the panel: 'The difference in visual presentation does NOT come from different emotions or arbitrary random selection; it comes strictly from Member 4's personalized LinUCB user modeling constrained to Member 2's emotion-safe candidate space.'",
        "Conclude with technical honesty: Member 3 transition smoothing and Member 2 final Three.js rendering are simulated previews and will be connected in group integration.",
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
                Interactive Walkthrough & Demo Guide
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
