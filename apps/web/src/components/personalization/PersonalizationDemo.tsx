import React, { useState, useEffect, useCallback, useRef } from "react";
import type {
  RecommendationResponse,
  FeedbackResponse,
  UserPersonalizationStateData,
  FeedbackType,
  MERTier3Event,
  FeedbackEvent,
} from "../../types/personalization";
import {
  getSimulatedMember2Output,
  PRESET_REGISTRY,
} from "../../types/personalization";
import {
  getRecommendation,
  submitFeedback,
  getUserState,
  checkBackendHealth,
  resetDemoUsers,
} from "../../api/personalizationApi";
import { UserSelector } from "./UserSelector";
import { EmotionControl } from "./EmotionControl";
import { VisualPreviewCanvas } from "./VisualPreviewCanvas";
import { RecommendationCard } from "./RecommendationCard";
import { FeedbackControls } from "./FeedbackControls";
import { UserLearningPanel } from "./UserLearningPanel";
import { PersonalizationComparison } from "./PersonalizationComparison";
import { TechnicalDetailsPanel } from "./TechnicalDetailsPanel";
import { VivaWalkthroughModal } from "./VivaWalkthroughModal";

export const PersonalizationDemo: React.FC = () => {
  // Active user selection (isolated integration demo users)
  const [currentUserId, setCurrentUserId] = useState<string>("demo-integration-user-a");
  const [sessionId, setSessionId] = useState<string>("session-demo-001");

  // Emotion sliders (defaults: Happy baseline context V = 0.70, A = 0.40)
  const [valence, setValence] = useState<number>(0.7);
  const [arousal, setArousal] = useState<number>(0.4);

  // Sequences and simulation audio time
  const [recSequence, setRecSequence] = useState<number>(0);
  const [audioTimeMs, setAudioTimeMs] = useState<number>(1000);

  // Recommendation & feedback state
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [lastFeedback, setLastFeedback] = useState<FeedbackResponse | null>(null);
  const [feedbackSubmittedForCurrentRec, setFeedbackSubmittedForCurrentRec] = useState<boolean>(false);

  // User states
  const [activeUserState, setActiveUserState] = useState<UserPersonalizationStateData | null>(null);
  const [stateA, setStateA] = useState<UserPersonalizationStateData | null>(null);
  const [stateB, setStateB] = useState<UserPersonalizationStateData | null>(null);

  // Latest recommendation snapshots per user to evaluate candidate-aware same-context divergence
  const [recA, setRecA] = useState<{
    recommended_preset_id: string;
    valence: number;
    arousal: number;
    strategy: string;
    candidates?: string[];
    default_visual_id?: string;
  } | null>(null);
  const [recB, setRecB] = useState<{
    recommended_preset_id: string;
    valence: number;
    arousal: number;
    strategy: string;
    candidates?: string[];
    default_visual_id?: string;
  } | null>(null);

  // Simulated Member 2 Candidate Generation based on current emotion compatibility
  const m2Output = getSimulatedMember2Output(valence, arousal);

  // Status flags
  const [isLoadingRec, setIsLoadingRec] = useState<boolean>(false);
  const [isSubmittingFb, setIsSubmittingFb] = useState<boolean>(false);
  const [isLoadingState, setIsLoadingState] = useState<boolean>(false);
  const [isResettingDemo, setIsResettingDemo] = useState<boolean>(false);
  const [backendHealth, setBackendHealth] = useState<{ online: boolean; message: string }>({
    online: true,
    message: "Checking connection...",
  });
  const [apiError, setApiError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const [isWalkthroughOpen, setIsWalkthroughOpen] = useState<boolean>(false);

  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((text: string, type: "success" | "error" | "info" = "info") => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToast({ text, type });
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
    }, 4500);
  }, []);

  // Fetch state for a specific user
  const fetchSingleUserState = useCallback(async (userId: string) => {
    try {
      return await getUserState(userId);
    } catch (err: any) {
      console.warn(`Failed to fetch state for ${userId}:`, err);
      return null;
    }
  }, []);

  // Refresh both User A and User B comparison states
  const refreshComparisonStates = useCallback(async () => {
    setIsLoadingState(true);
    try {
      const [uA, uB] = await Promise.all([
        fetchSingleUserState("demo-integration-user-a"),
        fetchSingleUserState("demo-integration-user-b"),
      ]);
      setStateA(uA);
      setStateB(uB);
      if (currentUserId === "demo-integration-user-a") setActiveUserState(uA);
      else if (currentUserId === "demo-integration-user-b") setActiveUserState(uB);
    } catch (err: any) {
      console.error("Error refreshing comparison states:", err);
    } finally {
      setIsLoadingState(false);
    }
  }, [currentUserId, fetchSingleUserState]);

  // Initial connection check & load state
  useEffect(() => {
    checkBackendHealth().then((health) => {
      setBackendHealth(health);
      if (!health.online) {
        setApiError(
          `Cannot reach FastAPI backend server. Ensure "uvicorn app.main:app" is running at http://localhost:8000.`
        );
      }
    });

    refreshComparisonStates();
  }, [refreshComparisonStates]);

  // Switch user profile
  const handleSelectUser = async (newUserId: string) => {
    if (newUserId === currentUserId) return;
    setCurrentUserId(newUserId);
    setRecommendation(null);
    setLastFeedback(null);
    setFeedbackSubmittedForCurrentRec(false);
    setApiError(null);

    // Switch session stream per user to keep sequence scoped
    setSessionId(`session-${newUserId}-${Date.now().toString().slice(-4)}`);
    setRecSequence(0);

    // Load user state
    setIsLoadingState(true);
    try {
      const userState = await fetchSingleUserState(newUserId);
      setActiveUserState(userState);
      if (newUserId === "demo-integration-user-a") setStateA(userState);
      if (newUserId === "demo-integration-user-b") setStateB(userState);
      showToast(`Switched active profile to ${newUserId === "demo-integration-user-a" ? "User A" : "User B"}`, "info");
    } finally {
      setIsLoadingState(false);
    }
  };

  // Refresh active user state with visual feedback and toast
  const handleRefreshActiveUserState = async () => {
    setIsLoadingState(true);
    try {
      const state = await fetchSingleUserState(currentUserId);
      setActiveUserState(state);
      if (currentUserId === "demo-integration-user-a") setStateA(state);
      if (currentUserId === "demo-integration-user-b") setStateB(state);

      const updates = state?.successful_learning_updates ?? 0;
      const userName = currentUserId === "demo-integration-user-a" ? "User A" : "User B";
      showToast(`PostgreSQL state refreshed for ${userName} (${updates} learning updates recorded).`, "info");
    } catch (err: any) {
      console.error("Failed to refresh user state:", err);
      showToast("Failed to refresh user state from PostgreSQL.", "error");
    } finally {
      setIsLoadingState(false);
    }
  };

  // Reset demo users back to cold start baseline (clears DB records & bandit model)
  const handleResetDemoUsers = async () => {
    if (isResettingDemo || isLoadingRec || isSubmittingFb) return;
    setIsResettingDemo(true);
    setApiError(null);
    try {
      await resetDemoUsers();
      // Clear local recommendation, feedback, and comparison states
      setRecommendation(null);
      setLastFeedback(null);
      setFeedbackSubmittedForCurrentRec(false);
      setRecSequence(0);
      setRecA(null);
      setRecB(null);
      setSessionId(`session-${currentUserId}-${Date.now().toString().slice(-4)}`);

      // Refresh both user states from PostgreSQL
      await refreshComparisonStates();
      showToast(
        "Demo users reset to Cold Start baseline (0 learning updates). Ready for live presentation!",
        "success"
      );
    } catch (err: any) {
      console.error("Failed to reset demo users:", err);
      const msg = err?.message || "Failed to reset demo users in backend database.";
      setApiError(msg);
      showToast(`Reset failed: ${msg}`, "error");
    } finally {
      setIsResettingDemo(false);
    }
  };

  // Get Recommendation
  const handleGetRecommendation = async () => {
    setIsLoadingRec(true);
    setApiError(null);

    const nextSeq = recSequence;
    const nextTime = audioTimeMs + 1000;

    const tier3Event: MERTier3Event = {
      schema_version: "1.1",
      event_type: "mer.tier3",
      session_id: sessionId,
      sequence: nextSeq,
      audio_time_ms: nextTime,
      emotion: {
        valence: Math.round(valence * 100) / 100,
        arousal: Math.round(arousal * 100) / 100,
        confidence: 0.95,
      },
    };

    try {
      const rec = await getRecommendation(
        currentUserId,
        tier3Event,
        m2Output.candidateVisualIds,
        m2Output.defaultVisualId
      );
      setRecommendation(rec);
      setFeedbackSubmittedForCurrentRec(false);
      setRecSequence(nextSeq + 1);
      setAudioTimeMs(nextTime);

      const snapshot = {
        recommended_preset_id: rec.recommended_preset_id,
        valence: Math.round(valence * 100) / 100,
        arousal: Math.round(arousal * 100) / 100,
        strategy: rec.strategy,
        candidates: m2Output.candidateVisualIds,
        default_visual_id: m2Output.defaultVisualId,
      };

      if (currentUserId === "demo-integration-user-a") {
        setRecA(snapshot);
      } else if (currentUserId === "demo-integration-user-b") {
        setRecB(snapshot);
      }

      showToast(
        `Recommendation received: ${rec.recommended_preset_id} (${rec.strategy === "linucb" ? "LinUCB" : "Cold Start"})`,
        "success"
      );

      // Refresh states
      await refreshComparisonStates();
    } catch (err: any) {
      console.error("Failed to get recommendation:", err);
      setApiError(err.message || "Failed to generate recommendation from backend.");
      showToast(err.message || "Failed to generate recommendation.", "error");
    } finally {
      setIsLoadingRec(false);
    }
  };

  // Submit Feedback
  const handleSubmitFeedback = async (
    type: FeedbackType,
    rating?: number
  ): Promise<FeedbackResponse> => {
    if (!recommendation) {
      throw new Error("No active recommendation to give feedback for.");
    }

    setIsSubmittingFb(true);
    setApiError(null);

    const fbEvent: FeedbackEvent = {
      schema_version: "1.1",
      event_type: "feedback.event",
      session_id: recommendation.session_id,
      sequence: recommendation.sequence + 1,
      audio_time_ms: recommendation.audio_time_ms + 500,
      feedback_id: `fb_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      preset_id: recommendation.recommended_preset_id,
      feedback: {
        type: type,
        ...(rating !== undefined ? { rating } : {}),
      },
    };

    try {
      const res = await submitFeedback(currentUserId, fbEvent);
      setLastFeedback(res);
      setFeedbackSubmittedForCurrentRec(true);

      showToast(
        `Feedback applied! Reward: ${res.reward !== null ? (res.reward! > 0 ? `+${res.reward}` : res.reward) : 0} | Bandit model updated for ${recommendation.recommended_preset_id}.`,
        "success"
      );

      // Refresh states
      await refreshComparisonStates();
      return res;
    } catch (err: any) {
      console.error("Failed to submit feedback:", err);
      setApiError(err.message || "Failed to submit feedback event.");
      showToast(err.message || "Feedback submission failed.", "error");
      throw err;
    } finally {
      setIsSubmittingFb(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "1350px",
        margin: "0 auto",
        padding: "1.5rem 1.25rem 3rem 1.25rem",
        color: "#e2e8f0",
        fontFamily:
          'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {/* Toast Notification Banner */}
      {toast && (
        <div
          style={{
            position: "fixed",
            bottom: "1.5rem",
            right: "1.5rem",
            padding: "0.85rem 1.25rem",
            borderRadius: "0.6rem",
            backgroundColor:
              toast.type === "success"
                ? "rgba(6, 78, 59, 0.95)"
                : toast.type === "error"
                ? "rgba(127, 29, 29, 0.95)"
                : "rgba(30, 58, 138, 0.95)",
            color: "#ffffff",
            border: `1px solid ${
              toast.type === "success"
                ? "#10b981"
                : toast.type === "error"
                ? "#f43f5e"
                : "#38bdf8"
            }`,
            boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.6)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            fontSize: "0.88rem",
            fontWeight: 600,
            backdropFilter: "blur(8px)",
            animation: "slideUp 0.3s ease",
          }}
        >
          <span>
            {toast.type === "success"
              ? "✅"
              : toast.type === "error"
              ? "❌"
              : "ℹ️"}
          </span>
          <span>{toast.text}</span>
        </div>
      )}

      {/* Top Header Card */}
      <header
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.8)",
          borderRadius: "0.85rem",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          padding: "1.25rem 1.5rem",
          marginBottom: "1rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          backdropFilter: "blur(12px)",
          boxShadow: "0 8px 24px -4px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
            <h1
              style={{
                fontSize: "1.6rem",
                fontWeight: 800,
                margin: 0,
                color: "#f8fafc",
                letterSpacing: "-0.02em",
              }}
            >
              Candidate-Aware Adaptive Visual Personalization
            </h1>
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 800,
                letterSpacing: "0.08em",
                padding: "0.25rem 0.6rem",
                borderRadius: "0.375rem",
                backgroundColor: "rgba(245, 158, 11, 0.2)",
                color: "#fbbf24",
                border: "1px solid rgba(245, 158, 11, 0.45)",
              }}
            >
              DEMO / SIMULATION MODE
            </span>
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 600,
                padding: "0.25rem 0.6rem",
                borderRadius: "0.375rem",
                backgroundColor: backendHealth.online
                  ? "rgba(16, 185, 129, 0.2)"
                  : "rgba(244, 63, 94, 0.2)",
                color: backendHealth.online ? "#34d399" : "#f87171",
                border: `1px solid ${
                  backendHealth.online
                    ? "rgba(16, 185, 129, 0.4)"
                    : "rgba(244, 63, 94, 0.4)"
                }`,
              }}
            >
              {backendHealth.online ? "● Backend Connected" : "○ Backend Offline"}
            </span>
          </div>

          <div style={{ fontSize: "0.85rem", color: "#38bdf8", fontWeight: 600, marginTop: "0.2rem" }}>
            Member 4: Adaptive Personalization & User Analytics (Member 2 Candidate Integration)
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={handleResetDemoUsers}
            disabled={isResettingDemo || isLoadingRec || isSubmittingFb}
            title="Reset both demo user profiles to Cold Start baseline (0 learning updates)"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.6rem 1.1rem",
              borderRadius: "0.5rem",
              backgroundColor: "rgba(239, 68, 68, 0.12)",
              border: "1.5px solid rgba(239, 68, 68, 0.4)",
              color: "#fca5a5",
              fontSize: "0.85rem",
              fontWeight: 700,
              cursor: isResettingDemo || isLoadingRec || isSubmittingFb ? "not-allowed" : "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <span
              style={{
                display: "inline-block",
                transform: isResettingDemo ? "rotate(180deg)" : "none",
                transition: "transform 0.5s ease",
              }}
            >
              ↺
            </span>
            <span>{isResettingDemo ? "Resetting Demo..." : "Reset Demo Users"}</span>
          </button>

          <button
            type="button"
            onClick={() => setIsWalkthroughOpen(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.6rem 1.1rem",
              borderRadius: "0.5rem",
              backgroundColor: "rgba(56, 189, 248, 0.15)",
              border: "1.5px solid rgba(56, 189, 248, 0.4)",
              color: "#38bdf8",
              fontSize: "0.85rem",
              fontWeight: 700,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <span>🎓</span>
            <span>Demo Walkthrough</span>
          </button>
        </div>
      </header>



      {/* 5-Stage Architecture & Component Ownership Pipeline Flow */}
      <div
        style={{
          backgroundColor: "rgba(15, 23, 42, 0.75)",
          borderRadius: "0.75rem",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          padding: "0.85rem 1rem",
          marginBottom: "1rem",
          backdropFilter: "blur(10px)",
        }}
      >
        <div style={{ fontSize: "0.72rem", color: "#94a3b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
          System Architecture & Component Ownership Flow
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "0.5rem",
            alignItems: "stretch",
          }}
        >
          {/* Member 1 */}
          <div
            style={{
              backgroundColor: "rgba(30, 41, 59, 0.5)",
              padding: "0.6rem 0.75rem",
              borderRadius: "0.45rem",
              border: "1px solid rgba(255, 255, 255, 0.06)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "#f8fafc" }}>Member 1</span>
              <span style={{ fontSize: "0.62rem", padding: "0.1rem 0.35rem", borderRadius: "0.25rem", backgroundColor: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", fontWeight: 700 }}>SIMULATED</span>
            </div>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#cbd5e1", marginTop: "0.2rem" }}>MER / Valence-Arousal</div>
            <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.15rem" }}>Audio → Emotion Context</div>
          </div>

          {/* Member 2 Candidate Gen */}
          <div
            style={{
              backgroundColor: "rgba(30, 41, 59, 0.5)",
              padding: "0.6rem 0.75rem",
              borderRadius: "0.45rem",
              border: "1px solid rgba(255, 255, 255, 0.06)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "#f8fafc" }}>Member 2</span>
              <span style={{ fontSize: "0.62rem", padding: "0.1rem 0.35rem", borderRadius: "0.25rem", backgroundColor: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", fontWeight: 700 }}>SIMULATED</span>
            </div>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#cbd5e1", marginTop: "0.2rem" }}>Candidate Generation</div>
            <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.15rem" }}>Emotion → Safe Visual IDs</div>
          </div>

          {/* Member 4 Personalization (LIVE) */}
          <div
            style={{
              backgroundColor: "rgba(56, 189, 248, 0.1)",
              padding: "0.6rem 0.75rem",
              borderRadius: "0.45rem",
              border: "1.5px solid rgba(56, 189, 248, 0.5)",
              boxShadow: "0 0 12px rgba(56, 189, 248, 0.2)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "#38bdf8" }}>Member 4</span>
              <span style={{ fontSize: "0.62rem", padding: "0.1rem 0.35rem", borderRadius: "0.25rem", backgroundColor: "rgba(16, 185, 129, 0.25)", color: "#34d399", fontWeight: 800 }}>REAL / LIVE</span>
            </div>
            <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#f8fafc", marginTop: "0.2rem" }}>Adaptive Personalization</div>
            <div style={{ fontSize: "0.68rem", color: "#93c5fd", marginTop: "0.15rem" }}>Disjoint LinUCB + History</div>
          </div>

          {/* Member 3 Transition */}
          <div
            style={{
              backgroundColor: "rgba(30, 41, 59, 0.35)",
              padding: "0.6rem 0.75rem",
              borderRadius: "0.45rem",
              border: "1px dashed rgba(255, 255, 255, 0.12)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "#94a3b8" }}>Member 3</span>
              <span style={{ fontSize: "0.62rem", padding: "0.1rem 0.35rem", borderRadius: "0.25rem", backgroundColor: "rgba(100, 116, 139, 0.2)", color: "#94a3b8", fontWeight: 600 }}>NOT CONNECTED</span>
            </div>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#94a3b8", marginTop: "0.2rem" }}>Transition Smoothing</div>
            <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.15rem" }}>Timing & Morph Buffer</div>
          </div>

          {/* Member 2 Renderer */}
          <div
            style={{
              backgroundColor: "rgba(30, 41, 59, 0.35)",
              padding: "0.6rem 0.75rem",
              borderRadius: "0.45rem",
              border: "1px dashed rgba(255, 255, 255, 0.12)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "#94a3b8" }}>Member 2</span>
              <span style={{ fontSize: "0.62rem", padding: "0.1rem 0.35rem", borderRadius: "0.25rem", backgroundColor: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", fontWeight: 600 }}>SIMULATED PREVIEW</span>
            </div>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#94a3b8", marginTop: "0.2rem" }}>Final Three.js Renderer</div>
            <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "0.15rem" }}>Canvas Demo (Preview only)</div>
          </div>
        </div>
      </div>

      {/* Demo Status & Simulation Disclosure Notice */}
      <div
        style={{
          padding: "0.75rem 1rem",
          borderRadius: "0.5rem",
          backgroundColor: "rgba(15, 23, 42, 0.6)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          marginBottom: "1.5rem",
          fontSize: "0.76rem",
          lineHeight: 1.5,
          color: "#94a3b8",
        }}
      >
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
          <div>
            <strong style={{ color: "#fbbf24" }}>SIMULATED:</strong> Member 1 MER emotion input • Member 2 Top-K candidate output • Member 2 visual preview.
          </div>
          <div>
            <strong style={{ color: "#34d399" }}>REAL:</strong> Member 4 candidate-aware recommendation • Disjoint LinUCB • user isolation • feedback-to-reward • PostgreSQL persistence.
          </div>
          <div>
            <strong style={{ color: "#38bdf8" }}>PENDING:</strong> Final Member 1 MER model • Member 2 runtime Top-K API • Member 3 transition smoothing • Member 2 Three.js renderer.
          </div>
        </div>
      </div>

      {/* Global Error Banner */}
      {apiError && (
        <div
          style={{
            backgroundColor: "rgba(127, 29, 29, 0.8)",
            color: "#fecaca",
            border: "1px solid #dc2626",
            padding: "0.85rem 1.25rem",
            borderRadius: "0.6rem",
            marginBottom: "1.5rem",
            fontSize: "0.88rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <strong>Error:</strong> {apiError}
          </div>
          <button
            type="button"
            onClick={() => setApiError(null)}
            style={{
              background: "transparent",
              border: "none",
              color: "#fecaca",
              cursor: "pointer",
              fontWeight: 700,
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Layout Content */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* Step 3: User Selector */}
        <UserSelector
          currentUserId={currentUserId}
          onSelectUser={handleSelectUser}
          sessionId={sessionId}
          disabled={isLoadingRec || isSubmittingFb}
          onResetDemoUsers={handleResetDemoUsers}
          isResetting={isResettingDemo}
        />


        {/* Two-Column Main Stage: Controls & Preview */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {/* Left Column: Emotion Input, Member 2 Candidates, & Recommendation Action */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <EmotionControl
              valence={valence}
              arousal={arousal}
              onValenceChange={setValence}
              onArousalChange={setArousal}
              disabled={isLoadingRec}
            />

            {/* Simulated Member 2 Candidate Generation Stage */}
            <div
              style={{
                backgroundColor: "rgba(30, 41, 59, 0.7)",
                borderRadius: "0.75rem",
                border: "1px solid rgba(56, 189, 248, 0.25)",
                padding: "1.1rem 1.25rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
                backdropFilter: "blur(12px)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "1.1rem" }}>🎨</span>
                  <h3 style={{ margin: 0, fontSize: "0.98rem", fontWeight: 700, color: "#f8fafc" }}>
                    SIMULATED MEMBER 2 OUTPUT
                  </h3>
                </div>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "0.15rem 0.5rem",
                    borderRadius: "0.3rem",
                    backgroundColor: "rgba(245, 158, 11, 0.15)",
                    color: "#fbbf24",
                    border: "1px solid rgba(245, 158, 11, 0.3)",
                  }}
                >
                  SIMULATED COMPATIBILITY
                </span>
              </div>

              <p style={{ margin: 0, fontSize: "0.75rem", color: "#94a3b8", lineHeight: 1.4 }}>
                Simulated from Member 2's current compatibility mapping. Final Member 2 Top-K runtime interface is not yet connected.
              </p>

              <div
                style={{
                  backgroundColor: "rgba(15, 23, 42, 0.65)",
                  borderRadius: "0.5rem",
                  padding: "0.85rem",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.65rem",
                  fontSize: "0.82rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ color: "#94a3b8" }}>Detected Emotion Category:</span>
                  <span
                    style={{
                      fontWeight: 800,
                      padding: "0.15rem 0.55rem",
                      borderRadius: "0.3rem",
                      backgroundColor:
                        m2Output.emotionCategory === "HAPPY"
                          ? "rgba(245, 158, 11, 0.2)"
                          : m2Output.emotionCategory === "CALM"
                          ? "rgba(16, 185, 129, 0.2)"
                          : m2Output.emotionCategory === "ENERGETIC"
                          ? "rgba(236, 72, 153, 0.2)"
                          : "rgba(56, 189, 248, 0.2)",
                      color:
                        m2Output.emotionCategory === "HAPPY"
                          ? "#fbbf24"
                          : m2Output.emotionCategory === "CALM"
                          ? "#34d399"
                          : m2Output.emotionCategory === "ENERGETIC"
                          ? "#f472b6"
                          : "#38bdf8",
                    }}
                  >
                    {m2Output.emotionCategory}
                  </span>
                </div>

                <div>
                  <span style={{ color: "#94a3b8", display: "block", marginBottom: "0.35rem" }}>
                    Emotion-Safe Candidates ({m2Output.candidateVisualIds.length}):
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                    {m2Output.candidateVisualIds.map((cid, idx) => {
                      const meta = PRESET_REGISTRY[cid];
                      const isDefault = cid === m2Output.defaultVisualId;
                      return (
                        <div
                          key={cid}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            padding: "0.35rem 0.6rem",
                            borderRadius: "0.35rem",
                            backgroundColor: isDefault
                              ? "rgba(56, 189, 248, 0.12)"
                              : "rgba(15, 23, 42, 0.65)",
                            border: `1px solid ${
                              isDefault ? "rgba(56, 189, 248, 0.35)" : "rgba(255, 255, 255, 0.08)"
                            }`,
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                            <span style={{ color: "#64748b", fontWeight: 700, fontSize: "0.75rem" }}>
                              {idx + 1}.
                            </span>
                            <span
                              style={{
                                width: "8px",
                                height: "8px",
                                borderRadius: "50%",
                                backgroundColor: meta?.accentColor || "#38bdf8",
                              }}
                            />
                            <span style={{ fontWeight: 600, color: "#f8fafc" }}>
                              {meta?.name || cid}
                            </span>
                            <code style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{cid}</code>
                          </div>
                          {isDefault && (
                            <span
                              style={{
                                fontSize: "0.68rem",
                                fontWeight: 700,
                                color: "#38bdf8",
                                backgroundColor: "rgba(56, 189, 248, 0.18)",
                                padding: "0.1rem 0.4rem",
                                borderRadius: "0.25rem",
                              }}
                            >
                              Member 2 Default
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingTop: "0.35rem",
                    borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                    fontSize: "0.75rem",
                  }}
                >
                  <span style={{ color: "#94a3b8" }}>Member 2 Default Candidate:</span>
                  <code style={{ color: "#38bdf8", fontWeight: 700 }}>{m2Output.defaultVisualId}</code>
                </div>
              </div>
            </div>

            <RecommendationCard
              recommendation={recommendation}
              isLoading={isLoadingRec}
              onGetRecommendation={handleGetRecommendation}
              valence={valence}
              arousal={arousal}
              candidates={m2Output.candidateVisualIds}
              defaultVisualId={m2Output.defaultVisualId}
              disabled={!backendHealth.online}
            />
          </div>

          {/* Right Column: Visual Preview & Feedback */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <VisualPreviewCanvas
              presetId={recommendation?.recommended_preset_id || null}
              strategy={recommendation?.strategy || null}
              score={recommendation?.score ?? null}
              valence={valence}
              arousal={arousal}
            />

            <FeedbackControls
              hasActiveRecommendation={recommendation !== null}
              recommendedPresetId={recommendation?.recommended_preset_id || null}
              onSubmitFeedback={handleSubmitFeedback}
              isSubmitting={isSubmittingFb}
              lastFeedbackResponse={lastFeedback}
              feedbackSubmittedForCurrentRec={feedbackSubmittedForCurrentRec}
              disabled={!backendHealth.online}
            />
          </div>
        </div>

        {/* Step 9 & 10: Learning Analytics and Cross-User Comparison */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
            gap: "1.5rem",
          }}
        >
          <UserLearningPanel
            userState={activeUserState}
            userId={currentUserId}
            isLoading={isLoadingState}
            onRefresh={handleRefreshActiveUserState}
          />

          <PersonalizationComparison
            stateA={stateA}
            stateB={stateB}
            recA={recA}
            recB={recB}
            onRefreshBoth={refreshComparisonStates}
            isLoading={isLoadingState}
          />
        </div>

        {/* Step 16: Collapsible Technical Reference Panel */}
        <TechnicalDetailsPanel
          valence={valence}
          arousal={arousal}
          recommendation={recommendation}
          lastFeedback={lastFeedback}
          userId={currentUserId}
          candidates={m2Output.candidateVisualIds}
          defaultVisualId={m2Output.defaultVisualId}
        />
      </div>

      {/* Step 14: Viva Script Modal */}
      <VivaWalkthroughModal
        isOpen={isWalkthroughOpen}
        onClose={() => setIsWalkthroughOpen(false)}
      />
    </div>
  );
};
