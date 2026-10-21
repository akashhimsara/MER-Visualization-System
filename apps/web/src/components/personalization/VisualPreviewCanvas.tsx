import React, { useEffect, useRef } from "react";
import { PRESET_REGISTRY, type PresetMetadata } from "../../types/personalization";

interface VisualPreviewCanvasProps {
  presetId: string | null;
  strategy?: string | null;
  score?: number | null;
  valence: number;
  arousal: number;
}

export const VisualPreviewCanvas: React.FC<VisualPreviewCanvasProps> = ({
  presetId,
  strategy,
  score,
  valence,
  arousal,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const activePreset: PresetMetadata =
    (presetId && PRESET_REGISTRY[presetId]) || {
      id: "none",
      name: "Idle Ambient State",
      description: "Awaiting recommendation from personalization engine...",
      accentColor: "#64748b",
      secondaryColor: "#334155",
      moodQuadrant: "Neutral Baseline",
    };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    // Handle high DPI
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };

    resize();
    window.addEventListener("resize", resize);

    // Particle pool for ambient visualization
    const particles = Array.from({ length: 48 }, (_, i) => ({
      x: Math.random() * 800,
      y: Math.random() * 400,
      baseRadius: 2 + Math.random() * 4,
      speedX: (Math.random() - 0.5) * 1.5,
      speedY: (Math.random() - 0.5) * 1.5,
      phase: (i / 48) * Math.PI * 2,
    }));

    const render = () => {
      const width = canvas.getBoundingClientRect().width;
      const height = canvas.getBoundingClientRect().height;

      // Dark background with subtle gradient
      const bgGrad = ctx.createLinearGradient(0, 0, width, height);
      if (presetId === "mock-energetic-positive") {
        bgGrad.addColorStop(0, "#1a0f05");
        bgGrad.addColorStop(0.5, "#250d18");
        bgGrad.addColorStop(1, "#0f0714");
      } else if (presetId === "mock-calm-positive") {
        bgGrad.addColorStop(0, "#051814");
        bgGrad.addColorStop(0.5, "#061724");
        bgGrad.addColorStop(1, "#07111c");
      } else if (presetId === "mock-tense-negative") {
        bgGrad.addColorStop(0, "#22050b");
        bgGrad.addColorStop(0.5, "#180518");
        bgGrad.addColorStop(1, "#0f050b");
      } else if (presetId === "mock-calm-negative") {
        bgGrad.addColorStop(0, "#060914");
        bgGrad.addColorStop(0.5, "#0b0e1a");
        bgGrad.addColorStop(1, "#080b12");
      } else {
        bgGrad.addColorStop(0, "#0b0f19");
        bgGrad.addColorStop(1, "#080c14");
      }

      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      time += 0.02;

      // -------------------------------------------------------------
      // Specific Mood Generators
      // -------------------------------------------------------------
      if (presetId === "mock-energetic-positive") {
        // High energy, fast rotating radiant burst rings
        const rings = 4;
        for (let r = 0; r < rings; r++) {
          const radius = 45 + r * 38 + Math.sin(time * 3 + r) * 12;
          ctx.beginPath();
          ctx.arc(centerX, centerY, Math.max(10, radius), 0, Math.PI * 2);
          ctx.strokeStyle = r % 2 === 0 ? "rgba(245, 158, 11, 0.45)" : "rgba(236, 72, 153, 0.4)";
          ctx.lineWidth = 2 + (r % 2) * 1.5;
          ctx.stroke();
        }

        // Kinetic radial rays
        const rays = 16;
        for (let i = 0; i < rays; i++) {
          const angle = (i / rays) * Math.PI * 2 + time * 0.8;
          const innerR = 30 + Math.sin(time * 4 + i) * 8;
          const outerR = 140 + Math.cos(time * 5 + i * 2) * 35;
          ctx.beginPath();
          ctx.moveTo(centerX + Math.cos(angle) * innerR, centerY + Math.sin(angle) * innerR);
          ctx.lineTo(centerX + Math.cos(angle) * outerR, centerY + Math.sin(angle) * outerR);
          ctx.strokeStyle = "rgba(251, 146, 60, 0.6)";
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Core pulsating orb
        const coreGradient = ctx.createRadialGradient(
          centerX,
          centerY,
          4,
          centerX,
          centerY,
          50 + Math.sin(time * 6) * 10
        );
        coreGradient.addColorStop(0, "rgba(255, 237, 213, 0.95)");
        coreGradient.addColorStop(0.3, "rgba(245, 158, 11, 0.8)");
        coreGradient.addColorStop(1, "rgba(236, 72, 153, 0)");
        ctx.fillStyle = coreGradient;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 60, 0, Math.PI * 2);
        ctx.fill();
      } else if (presetId === "mock-calm-positive") {
        // Smooth undulating aurora ribbons
        const waves = 3;
        for (let w = 0; w < waves; w++) {
          ctx.beginPath();
          const waveOffset = w * 30;
          ctx.moveTo(0, centerY + waveOffset);
          for (let x = 0; x <= width; x += 15) {
            const y =
              centerY +
              waveOffset +
              Math.sin((x * 0.008) + time * 1.2 + w) * 32 +
              Math.cos((x * 0.015) - time * 0.8) * 16;
            ctx.lineTo(x, y);
          }
          ctx.strokeStyle =
            w === 0
              ? "rgba(16, 185, 129, 0.65)"
              : w === 1
              ? "rgba(6, 182, 212, 0.55)"
              : "rgba(52, 211, 153, 0.35)";
          ctx.lineWidth = 3.5;
          ctx.stroke();
        }

        // Soft floating halo
        const haloGrad = ctx.createRadialGradient(
          centerX,
          centerY,
          10,
          centerX,
          centerY,
          160
        );
        haloGrad.addColorStop(0, "rgba(16, 185, 129, 0.45)");
        haloGrad.addColorStop(0.6, "rgba(6, 182, 212, 0.2)");
        haloGrad.addColorStop(1, "rgba(15, 23, 42, 0)");
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 160, 0, Math.PI * 2);
        ctx.fill();
      } else if (presetId === "mock-tense-negative") {
        // Jagged polygon and chromatic tension spikes
        const points = 7;
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(time * 0.5);

        // Multiple jittery polygon outlines
        for (let layer = 0; layer < 3; layer++) {
          ctx.beginPath();
          const radiusBase = 65 + layer * 25;
          for (let i = 0; i <= points; i++) {
            const angle = (i / points) * Math.PI * 2;
            const jitter = ((i + layer) % 2 === 0 ? 30 : -25) * Math.sin(time * 5 + i * 3);
            const r = radiusBase + jitter;
            const px = Math.cos(angle) * r;
            const py = Math.sin(angle) * r;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.strokeStyle =
            layer === 0
              ? "rgba(244, 63, 94, 0.85)"
              : layer === 1
              ? "rgba(168, 85, 247, 0.65)"
              : "rgba(225, 29, 72, 0.4)";
          ctx.lineWidth = 2.5;
          ctx.stroke();
        }
        ctx.restore();

        // Tension flashes / strobe cross lines
        ctx.beginPath();
        ctx.moveTo(centerX - 100 + Math.sin(time * 8) * 20, centerY);
        ctx.lineTo(centerX + 100 + Math.sin(time * 8) * 20, centerY);
        ctx.moveTo(centerX, centerY - 70 + Math.cos(time * 7) * 20);
        ctx.lineTo(centerX, centerY + 70 + Math.cos(time * 7) * 20);
        ctx.strokeStyle = "rgba(244, 63, 94, 0.5)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else if (presetId === "mock-calm-negative") {
        // Deep slow drift, heavy particles, slow breathing fog
        const breathingRadius = 80 + Math.sin(time * 0.7) * 25;
        const mistGrad = ctx.createRadialGradient(
          centerX,
          centerY,
          5,
          centerX,
          centerY,
          breathingRadius + 70
        );
        mistGrad.addColorStop(0, "rgba(99, 102, 241, 0.35)");
        mistGrad.addColorStop(0.5, "rgba(30, 41, 59, 0.45)");
        mistGrad.addColorStop(1, "rgba(8, 12, 20, 0)");
        ctx.fillStyle = mistGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, breathingRadius + 70, 0, Math.PI * 2);
        ctx.fill();

        // Slow concentric quiet rings
        for (let i = 1; i <= 3; i++) {
          ctx.beginPath();
          ctx.arc(centerX, centerY, i * 45 + Math.sin(time * 0.5 + i) * 8, 0, Math.PI * 2);
          ctx.strokeStyle = "rgba(148, 163, 184, 0.15)";
          ctx.lineWidth = 1.2;
          ctx.stroke();
        }
      } else {
        // Idle default state: subtle breathing circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, 50 + Math.sin(time * 1.5) * 6, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(100, 116, 139, 0.3)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // -------------------------------------------------------------
      // Dynamic ambient particles reflecting active mood speed
      // -------------------------------------------------------------
      const speedMultiplier =
        presetId === "mock-energetic-positive"
          ? 2.2
          : presetId === "mock-tense-negative"
          ? 1.8
          : presetId === "mock-calm-positive"
          ? 0.7
          : 0.4;

      particles.forEach((p) => {
        p.x += p.speedX * speedMultiplier;
        p.y += p.speedY * speedMultiplier;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        const pulse = Math.sin(time * 2 + p.phase) * 1.5;
        const currentRadius = Math.max(1, p.baseRadius + pulse);

        ctx.beginPath();
        ctx.arc(p.x, p.y, currentRadius, 0, Math.PI * 2);

        if (presetId === "mock-energetic-positive") {
          ctx.fillStyle = "rgba(251, 191, 36, 0.65)";
        } else if (presetId === "mock-calm-positive") {
          ctx.fillStyle = "rgba(52, 211, 153, 0.55)";
        } else if (presetId === "mock-tense-negative") {
          ctx.fillStyle = "rgba(244, 63, 94, 0.6)";
        } else if (presetId === "mock-calm-negative") {
          ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
        } else {
          ctx.fillStyle = "rgba(100, 116, 139, 0.3)";
        }
        ctx.fill();
      });

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationId);
    };
  }, [presetId]);

  return (
    <div
      style={{
        position: "relative",
        borderRadius: "0.75rem",
        overflow: "hidden",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        backgroundColor: "#090d16",
        boxShadow: "0 10px 30px -5px rgba(0, 0, 0, 0.5)",
      }}
    >
      {/* Top Banner Disclaimer & Badges */}
      <div
        style={{
          position: "absolute",
          top: "0.75rem",
          left: "0.75rem",
          right: "0.75rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          zIndex: 10,
          pointerEvents: "none",
        }}
      >
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              letterSpacing: "0.06em",
              padding: "0.25rem 0.6rem",
              borderRadius: "0.375rem",
              backgroundColor: "rgba(15, 23, 42, 0.85)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              backdropFilter: "blur(6px)",
            }}
          >
            DEMO VISUAL PREVIEW
          </span>
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 600,
              padding: "0.2rem 0.5rem",
              borderRadius: "0.375rem",
              backgroundColor: "rgba(245, 158, 11, 0.18)",
              color: "#fbbf24",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              backdropFilter: "blur(6px)",
            }}
          >
            SIMULATION ONLY • Member 2 final visualization integration pending
          </span>
        </div>

        {strategy && (
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              padding: "0.25rem 0.65rem",
              borderRadius: "0.375rem",
              backgroundColor:
                strategy === "linucb"
                  ? "rgba(168, 85, 247, 0.25)"
                  : "rgba(16, 185, 129, 0.2)",
              color: strategy === "linucb" ? "#c084fc" : "#34d399",
              border: `1px solid ${
                strategy === "linucb"
                  ? "rgba(168, 85, 247, 0.5)"
                  : "rgba(16, 185, 129, 0.4)"
              }`,
              backdropFilter: "blur(6px)",
            }}
          >
            {strategy === "linucb" ? "⚡ LinUCB Model" : "❄️ Cold Start"}
          </span>
        )}
      </div>

      {/* 60FPS Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          width: "100%",
          height: "260px",
          display: "block",
        }}
      />

      {/* Bottom Metadata Overlay */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: "0.75rem 1rem",
          background:
            "linear-gradient(to top, rgba(9, 13, 22, 0.95) 0%, rgba(9, 13, 22, 0.6) 70%, transparent 100%)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: activePreset.accentColor,
                boxShadow: `0 0 10px ${activePreset.accentColor}`,
              }}
            />
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "#f8fafc" }}>
              {activePreset.name}
            </span>
            <code
              style={{
                fontSize: "0.75rem",
                color: "#94a3b8",
                backgroundColor: "rgba(255,255,255,0.06)",
                padding: "0.1rem 0.35rem",
                borderRadius: "0.25rem",
              }}
            >
              {activePreset.id}
            </code>
          </div>
          <p
            style={{
              margin: "0.25rem 0 0 0",
              fontSize: "0.78rem",
              color: "#94a3b8",
              maxWidth: "500px",
            }}
          >
            {activePreset.description} • Member 2 final visualization integration pending (Member 3 transition integration pending).
          </p>
        </div>

        <div style={{ textAlign: "right", fontSize: "0.75rem", color: "#64748b" }}>
          <div>
            Emotion Context:{" "}
            <span style={{ color: "#38bdf8", fontWeight: 600 }}>V: {valence.toFixed(2)}</span>,{" "}
            <span style={{ color: "#f43f5e", fontWeight: 600 }}>A: {arousal.toFixed(2)}</span>
          </div>
          {score !== null && score !== undefined && (
            <div style={{ marginTop: "0.15rem" }}>
              UCB Score:{" "}
              <span style={{ color: "#a855f7", fontWeight: 600 }}>
                {typeof score === "number" ? score.toFixed(4) : score}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
