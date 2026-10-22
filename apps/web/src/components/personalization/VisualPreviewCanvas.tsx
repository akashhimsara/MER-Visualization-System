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
      if (presetId === "COSMIC_BLOOM" || presetId === "mock-energetic-positive") {
        bgGrad.addColorStop(0, "#1f0917");
        bgGrad.addColorStop(0.5, "#2d0b1e");
        bgGrad.addColorStop(1, "#120516");
      } else if (presetId === "PARTICLE_AURORA" || presetId === "mock-calm-positive") {
        bgGrad.addColorStop(0, "#041b17");
        bgGrad.addColorStop(0.5, "#061a29");
        bgGrad.addColorStop(1, "#05101a");
      } else if (presetId === "NEON_MANDALA" || presetId === "mock-tense-negative") {
        bgGrad.addColorStop(0, "#1d0829");
        bgGrad.addColorStop(0.5, "#140624");
        bgGrad.addColorStop(1, "#090417");
      } else if (presetId === "COSMIC_IRIS" || presetId === "mock-calm-negative") {
        bgGrad.addColorStop(0, "#070817");
        bgGrad.addColorStop(0.5, "#0c0d24");
        bgGrad.addColorStop(1, "#050610");
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
      // Specific Mood & Visual Generators (Member 2 Visual Worlds)
      // -------------------------------------------------------------
      if (presetId === "COSMIC_BLOOM") {
        // COSMIC BLOOM: Multi-layered radiant floral petals and golden pulsing core
        const petals = 8;
        ctx.save();
        ctx.translate(centerX, centerY);

        // Layer 1: Outer blooming petal rings
        for (let layer = 0; layer < 3; layer++) {
          const layerRot = time * (0.2 + layer * 0.1) * (layer % 2 === 0 ? 1 : -1);
          ctx.rotate(layerRot);
          const baseR = 55 + layer * 32;
          ctx.beginPath();
          for (let i = 0; i <= petals * 2; i++) {
            const angle = (i / (petals * 2)) * Math.PI * 2;
            const amp = (layer === 0 ? 18 : 28) * Math.sin(time * 3 + layer);
            const r = baseR + Math.sin(angle * petals) * amp;
            const px = Math.cos(angle) * r;
            const py = Math.sin(angle) * r;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.strokeStyle =
            layer === 0
              ? "rgba(245, 158, 11, 0.75)"
              : layer === 1
              ? "rgba(236, 72, 153, 0.65)"
              : "rgba(251, 191, 36, 0.4)";
          ctx.lineWidth = 2.2;
          ctx.stroke();
        }
        ctx.restore();

        // Pulsating golden/magenta core
        const coreGradient = ctx.createRadialGradient(
          centerX,
          centerY,
          4,
          centerX,
          centerY,
          45 + Math.sin(time * 4) * 8
        );
        coreGradient.addColorStop(0, "rgba(255, 247, 237, 0.95)");
        coreGradient.addColorStop(0.35, "rgba(245, 158, 11, 0.75)");
        coreGradient.addColorStop(0.7, "rgba(236, 72, 153, 0.4)");
        coreGradient.addColorStop(1, "rgba(236, 72, 153, 0)");
        ctx.fillStyle = coreGradient;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 55, 0, Math.PI * 2);
        ctx.fill();
      } else if (presetId === "PARTICLE_AURORA" || presetId === "mock-calm-positive") {
        // PARTICLE AURORA: Harmonic undulating cyan/emerald wave ribbons
        const waves = 4;
        for (let w = 0; w < waves; w++) {
          ctx.beginPath();
          const waveOffset = (w - 1.5) * 28;
          ctx.moveTo(0, centerY + waveOffset);
          for (let x = 0; x <= width; x += 12) {
            const y =
              centerY +
              waveOffset +
              Math.sin(x * 0.007 + time * 1.1 + w * 0.8) * 30 +
              Math.cos(x * 0.014 - time * 0.7 + w) * 15;
            ctx.lineTo(x, y);
          }
          ctx.strokeStyle =
            w === 0
              ? "rgba(16, 185, 129, 0.7)"
              : w === 1
              ? "rgba(6, 182, 212, 0.6)"
              : w === 2
              ? "rgba(52, 211, 153, 0.45)"
              : "rgba(34, 211, 238, 0.3)";
          ctx.lineWidth = 3;
          ctx.stroke();
        }

        // Soft celestial atmospheric halo
        const haloGrad = ctx.createRadialGradient(centerX, centerY, 15, centerX, centerY, 150);
        haloGrad.addColorStop(0, "rgba(16, 185, 129, 0.35)");
        haloGrad.addColorStop(0.5, "rgba(6, 182, 212, 0.18)");
        haloGrad.addColorStop(1, "rgba(15, 23, 42, 0)");
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 150, 0, Math.PI * 2);
        ctx.fill();
      } else if (presetId === "NEON_MANDALA") {
        // NEON MANDALA: High-energy intricate sacred geometry, rotating polygon spokes
        const spokes = 12;
        ctx.save();
        ctx.translate(centerX, centerY);

        // Concentric geometric star rings
        for (let ring = 1; ring <= 4; ring++) {
          ctx.save();
          ctx.rotate(time * (0.35 / ring) * (ring % 2 === 0 ? -1 : 1));
          ctx.beginPath();
          const rBase = ring * 32 + Math.sin(time * 4 + ring) * 5;
          for (let s = 0; s <= spokes; s++) {
            const angle = (s / spokes) * Math.PI * 2;
            const r = s % 2 === 0 ? rBase : rBase * 0.65;
            const px = Math.cos(angle) * r;
            const py = Math.sin(angle) * r;
            if (s === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.strokeStyle =
            ring % 2 === 0 ? "rgba(168, 85, 247, 0.75)" : "rgba(56, 189, 248, 0.75)";
          ctx.lineWidth = 2;
          ctx.stroke();
          ctx.restore();
        }

        // Laser radial crosshairs
        for (let i = 0; i < spokes; i++) {
          const a = (i / spokes) * Math.PI * 2 + time * 0.6;
          ctx.beginPath();
          ctx.moveTo(Math.cos(a) * 20, Math.sin(a) * 20);
          ctx.lineTo(Math.cos(a) * 145, Math.sin(a) * 145);
          ctx.strokeStyle = "rgba(192, 132, 252, 0.4)";
          ctx.lineWidth = 1.2;
          ctx.stroke();
        }
        ctx.restore();

        // Pulsing geometric core
        ctx.beginPath();
        ctx.arc(centerX, centerY, 14 + Math.sin(time * 6) * 4, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.shadowColor = "#a855f7";
        ctx.shadowBlur = 15;
        ctx.fill();
        ctx.shadowBlur = 0;
      } else if (presetId === "COSMIC_IRIS" || presetId === "mock-calm-negative") {
        // COSMIC IRIS: Void portal with deep swirling dark indigo/violet accretion rings
        const portalRadius = 55 + Math.sin(time * 0.9) * 10;

        // Outer swirling celestial accretion spirals
        for (let ring = 1; ring <= 5; ring++) {
          ctx.beginPath();
          const r = portalRadius + ring * 22;
          ctx.arc(centerX, centerY, r, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.4 - ring * 0.06})`;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        // Accretion disk glow
        const accretionGrad = ctx.createRadialGradient(
          centerX,
          centerY,
          portalRadius * 0.5,
          centerX,
          centerY,
          portalRadius + 60
        );
        accretionGrad.addColorStop(0, "rgba(5, 6, 15, 0.95)");
        accretionGrad.addColorStop(0.4, "rgba(99, 102, 241, 0.45)");
        accretionGrad.addColorStop(0.8, "rgba(139, 92, 246, 0.2)");
        accretionGrad.addColorStop(1, "rgba(5, 6, 15, 0)");
        ctx.fillStyle = accretionGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, portalRadius + 60, 0, Math.PI * 2);
        ctx.fill();

        // Central dark void aperture with glowing event horizon
        ctx.beginPath();
        ctx.arc(centerX, centerY, portalRadius * 0.55, 0, Math.PI * 2);
        ctx.fillStyle = "#03040a";
        ctx.fill();
        ctx.strokeStyle = "rgba(167, 139, 250, 0.85)";
        ctx.lineWidth = 2.5;
        ctx.stroke();
      } else if (presetId === "mock-energetic-positive") {
        // High energy, fast rotating radiant burst rings (fallback)
        const rings = 4;
        for (let r = 0; r < rings; r++) {
          const radius = 45 + r * 38 + Math.sin(time * 3 + r) * 12;
          ctx.beginPath();
          ctx.arc(centerX, centerY, Math.max(10, radius), 0, Math.PI * 2);
          ctx.strokeStyle = r % 2 === 0 ? "rgba(245, 158, 11, 0.45)" : "rgba(236, 72, 153, 0.4)";
          ctx.lineWidth = 2 + (r % 2) * 1.5;
          ctx.stroke();
        }
      } else if (presetId === "mock-tense-negative") {
        // Jagged polygon and chromatic tension spikes (fallback)
        const points = 7;
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(time * 0.5);
        ctx.beginPath();
        for (let i = 0; i <= points; i++) {
          const angle = (i / points) * Math.PI * 2;
          const r = 70 + (i % 2 === 0 ? 25 : -20);
          const px = Math.cos(angle) * r;
          const py = Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.strokeStyle = "rgba(244, 63, 94, 0.85)";
        ctx.lineWidth = 2.5;
        ctx.stroke();
        ctx.restore();
      } else {
        // Idle default state: subtle breathing circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, 50 + Math.sin(time * 1.5) * 6, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(100, 116, 139, 0.3)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // -------------------------------------------------------------
      // Dynamic ambient particles reflecting active visual mood
      // -------------------------------------------------------------
      const speedMultiplier =
        presetId === "COSMIC_BLOOM"
          ? 1.4
          : presetId === "PARTICLE_AURORA"
          ? 0.8
          : presetId === "NEON_MANDALA"
          ? 2.2
          : presetId === "COSMIC_IRIS"
          ? 0.5
          : presetId === "mock-energetic-positive"
          ? 2.0
          : 0.7;

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

        if (presetId === "COSMIC_BLOOM") {
          ctx.fillStyle = "rgba(244, 114, 182, 0.7)";
        } else if (presetId === "PARTICLE_AURORA") {
          ctx.fillStyle = "rgba(52, 211, 153, 0.65)";
        } else if (presetId === "NEON_MANDALA") {
          ctx.fillStyle = "rgba(192, 132, 252, 0.75)";
        } else if (presetId === "COSMIC_IRIS") {
          ctx.fillStyle = "rgba(129, 140, 248, 0.5)";
        } else if (presetId === "mock-energetic-positive") {
          ctx.fillStyle = "rgba(251, 191, 36, 0.65)";
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
            SIMULATED MEMBER 2 RENDERER
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
            Demo visual preview — final Member 2 Three.js renderer not connected
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
