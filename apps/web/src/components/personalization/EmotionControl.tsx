import React, { useRef } from "react";

interface EmotionControlProps {
  valence: number;
  arousal: number;
  onValenceChange: (val: number) => void;
  onArousalChange: (val: number) => void;
  disabled?: boolean;
}

interface DemoPreset {
  label: string;
  tag: string;
  v: number;
  a: number;
  accent: string;
}

const DEMO_PRESETS: DemoPreset[] = [
  {
    label: "High Positive / High Arousal",
    tag: "Energetic",
    v: 0.8,
    a: 0.75,
    accent: "#f59e0b",
  },
  {
    label: "Calm Positive",
    tag: "Serene",
    v: 0.6,
    a: -0.6,
    accent: "#10b981",
  },
  {
    label: "Tense Negative",
    tag: "Agitated",
    v: -0.7,
    a: 0.7,
    accent: "#f43f5e",
  },
  {
    label: "Calm Negative",
    tag: "Subdued",
    v: -0.6,
    a: -0.5,
    accent: "#6366f1",
  },
];

export const EmotionControl: React.FC<EmotionControlProps> = ({
  valence,
  arousal,
  onValenceChange,
  onArousalChange,
  disabled = false,
}) => {
  const planeRef = useRef<HTMLDivElement | null>(null);

  // Handle click or drag on 2D emotion coordinate plane
  const handlePlanePointer = (e: React.PointerEvent<HTMLDivElement>) => {
    if (disabled) return;
    const plane = planeRef.current;
    if (!plane) return;

    const rect = plane.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Map [0, width] -> [-1, 1]
    const clampedX = Math.max(0, Math.min(rect.width, x));
    const newV = Math.round(((clampedX / rect.width) * 2 - 1) * 100) / 100;

    // Map [0, height] -> [+1, -1] (top is high arousal +1, bottom is low -1)
    const clampedY = Math.max(0, Math.min(rect.height, y));
    const newA = Math.round((1 - (clampedY / rect.height) * 2) * 100) / 100;

    onValenceChange(newV);
    onArousalChange(newA);
  };

  // Dot position in percentage
  const dotLeft = `${((valence + 1) / 2) * 100}%`;
  const dotTop = `${((1 - arousal) / 2) * 100}%`;

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
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
            Simulated Emotion Context (MER Tier 3)
          </h3>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 600,
              padding: "0.2rem 0.5rem",
              borderRadius: "0.375rem",
              backgroundColor: "rgba(56, 189, 248, 0.15)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.3)",
            }}
          >
            SIMULATED INPUT • Member 1 MER integration pending
          </span>
        </div>
        <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
          Simulates real-time Valence & Arousal values that would be emitted by Member 1's MER engine (Member 1 MER integration pending).
        </p>
      </div>

      {/* Quick Demo Preset Buttons */}
      <div>
        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.5rem" }}>
          Demo Emotion Presets (Quick Set):
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.5rem" }}>
          {DEMO_PRESETS.map((p) => {
            const isActive =
              Math.abs(valence - p.v) < 0.05 && Math.abs(arousal - p.a) < 0.05;
            return (
              <button
                key={p.label}
                type="button"
                disabled={disabled}
                onClick={() => {
                  onValenceChange(p.v);
                  onArousalChange(p.a);
                }}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "0.45rem 0.65rem",
                  borderRadius: "0.5rem",
                  backgroundColor: isActive
                    ? "rgba(56, 189, 248, 0.2)"
                    : "rgba(15, 23, 42, 0.6)",
                  border: `1px solid ${isActive ? p.accent : "rgba(255, 255, 255, 0.08)"}`,
                  color: isActive ? "#ffffff" : "#94a3b8",
                  cursor: disabled ? "not-allowed" : "pointer",
                  transition: "all 0.2s ease",
                  textAlign: "left",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <span
                    style={{
                      width: "6px",
                      height: "6px",
                      borderRadius: "50%",
                      backgroundColor: p.accent,
                    }}
                  />
                  <span style={{ fontSize: "0.78rem", fontWeight: 700 }}>{p.tag}</span>
                </div>
                <span style={{ fontSize: "0.68rem", opacity: 0.8, marginTop: "0.15rem" }}>
                  V={p.v > 0 ? `+${p.v.toFixed(2)}` : p.v.toFixed(2)}, A={p.a > 0 ? `+${p.a.toFixed(2)}` : p.a.toFixed(2)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: 2D Plane + Sliders */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "190px 1fr",
          gap: "1.25rem",
          alignItems: "center",
        }}
      >
        {/* 2D Circumplex Plane */}
        <div
          ref={planeRef}
          onPointerDown={handlePlanePointer}
          onPointerMove={(e) => {
            if (e.buttons === 1) handlePlanePointer(e);
          }}
          style={{
            position: "relative",
            width: "190px",
            height: "190px",
            backgroundColor: "#090d16",
            borderRadius: "0.6rem",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            cursor: disabled ? "not-allowed" : "crosshair",
            overflow: "hidden",
            userSelect: "none",
            touchAction: "none",
          }}
        >
          {/* Subtle quadrant tinting */}
          <div
            style={{
              position: "absolute",
              top: 0,
              right: 0,
              width: "50%",
              height: "50%",
              backgroundColor: "rgba(245, 158, 11, 0.05)",
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 0,
              right: 0,
              width: "50%",
              height: "50%",
              backgroundColor: "rgba(16, 185, 129, 0.05)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "50%",
              height: "50%",
              backgroundColor: "rgba(244, 63, 94, 0.05)",
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              width: "50%",
              height: "50%",
              backgroundColor: "rgba(99, 102, 241, 0.05)",
            }}
          />

          {/* Crosshair Axes */}
          <div
            style={{
              position: "absolute",
              left: "50%",
              top: 0,
              bottom: 0,
              width: "1px",
              backgroundColor: "rgba(255, 255, 255, 0.2)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: 0,
              right: 0,
              height: "1px",
              backgroundColor: "rgba(255, 255, 255, 0.2)",
            }}
          />

          {/* Quadrant Text Labels */}
          <span
            style={{
              position: "absolute",
              top: "4px",
              right: "6px",
              fontSize: "0.6rem",
              color: "#fbbf24",
              fontWeight: 700,
            }}
          >
            Energetic +
          </span>
          <span
            style={{
              position: "absolute",
              bottom: "4px",
              right: "6px",
              fontSize: "0.6rem",
              color: "#34d399",
              fontWeight: 700,
            }}
          >
            Calm +
          </span>
          <span
            style={{
              position: "absolute",
              top: "4px",
              left: "6px",
              fontSize: "0.6rem",
              color: "#f87171",
              fontWeight: 700,
            }}
          >
            - Tense
          </span>
          <span
            style={{
              position: "absolute",
              bottom: "4px",
              left: "6px",
              fontSize: "0.6rem",
              color: "#818cf8",
              fontWeight: 700,
            }}
          >
            - Subdued
          </span>

          {/* Active Coordinate Dot */}
          <div
            style={{
              position: "absolute",
              left: dotLeft,
              top: dotTop,
              width: "14px",
              height: "14px",
              borderRadius: "50%",
              backgroundColor: "#38bdf8",
              boxShadow: "0 0 12px #38bdf8, 0 0 4px #ffffff",
              border: "2px solid #ffffff",
              transform: "translate(-50%, -50%)",
              pointerEvents: "none",
              transition: "transform 0.05s ease",
            }}
          />
        </div>

        {/* Sliders Container */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Valence Slider */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#38bdf8" }}>
                Valence (Pleasantness)
              </span>
              <span
                style={{
                  fontSize: "0.85rem",
                  fontFamily: "monospace",
                  fontWeight: 700,
                  color: valence >= 0 ? "#10b981" : "#f43f5e",
                }}
              >
                {valence > 0 ? `+${valence.toFixed(2)}` : valence.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.05"
              disabled={disabled}
              value={valence}
              onChange={(e) => onValenceChange(parseFloat(e.target.value))}
              style={{
                width: "100%",
                accentColor: "#38bdf8",
                cursor: disabled ? "not-allowed" : "pointer",
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#64748b" }}>
              <span>-1.0 Negative</span>
              <span>0.0 Neutral</span>
              <span>+1.0 Positive</span>
            </div>
          </div>

          {/* Arousal Slider */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#f43f5e" }}>
                Arousal (Energy / Intensity)
              </span>
              <span
                style={{
                  fontSize: "0.85rem",
                  fontFamily: "monospace",
                  fontWeight: 700,
                  color: arousal >= 0 ? "#f59e0b" : "#6366f1",
                }}
              >
                {arousal > 0 ? `+${arousal.toFixed(2)}` : arousal.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.05"
              disabled={disabled}
              value={arousal}
              onChange={(e) => onArousalChange(parseFloat(e.target.value))}
              style={{
                width: "100%",
                accentColor: "#f43f5e",
                cursor: disabled ? "not-allowed" : "pointer",
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#64748b" }}>
              <span>-1.0 Low / Sleepy</span>
              <span>0.0 Moderate</span>
              <span>+1.0 High / Alert</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
