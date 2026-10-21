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
  getRecommendation,
  submitFeedback,
  getUserState,
  checkBackendHealth,
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
  // Active user selection
  const [currentUserId, setCurrentUserId] = useState<string>("demo-user-a");
  const [sessionId, setSessionId] = useState<string>("session-demo-001");

  // Emotion sliders (defaults: V = 0.80, A = 0.75)
  const [valence, setValence] = useState<number>(0.8);
  const [arousal, setArousal] = useState<number>(0.75);

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

  // Latest recommendation snapshots per user to evaluate same-context divergence
  const [recA, setRecA] = useState<{
    recommended_preset_id: string;
    valence: number;
    arousal: number;
    strategy: string;
  } | null>(null);
  const [recB, setRecB] = useState<{
    recommended_preset_id: string;
    valence: number;
    arousal: number;
    strategy: string;
  } | null>(null);

  // Status flags
  const [isLoadingRec, setIsLoadingRec] = useState<boolean>(false);
  const [isSubmittingFb, setIsSubmittingFb] = useState<boolean>(false);
  const [isLoadingState, setIsLoadingState] = useState<boolean>(false);
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
        fetchSingleUserState("demo-user-a"),
        fetchSingleUserState("demo-user-b"),
      ]);
      setStateA(uA);
      setStateB(uB);
      if (currentUserId === "demo-user-a") setActiveUserState(uA);
      else if (currentUserId === "demo-user-b") setActiveUserState(uB);
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
      if (newUserId === "demo-user-a") setStateA(userState);
      if (newUserId === "demo-user-b") setStateB(userState);
      showToast(`Switched active profile to ${newUserId === "demo-user-a" ? "User A" : "User B"}`, "info");
    } finally {
      setIsLoadingState(false);
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
      const rec = await getRecommendation(currentUserId, tier3Event);
      setRecommendation(rec);
      setFeedbackSubmittedForCurrentRec(false);
      setRecSequence(nextSeq + 1);
      setAudioTimeMs(nextTime);

      const snapshot = {
        recommended_preset_id: rec.recommended_preset_id,
        valence: Math.round(valence * 100) / 100,
        arousal: Math.round(arousal * 100) / 100,
        strategy: rec.strategy,
      };

      if (currentUserId === "demo-user-a") {
        setRecA(snapshot);
      } else if (currentUserId === "demo-user-b") {
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
        `Feedback applied! Reward: ${res.reward !== null ? (res.reward! > 0 ? `+${res.reward}` : res.reward) : 0} | Bandit model updated.`,
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
          marginBottom: "1.5rem",
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
              Emotion-Adaptive Visual Personalization
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
              DEMO MODE
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
            Member 4: Adaptive Personalization & User Analytics
          </div>

          <p
            style={{
              margin: "0.35rem 0 0 0",
              fontSize: "0.8rem",
              color: "#94a3b8",
              fontStyle: "italic",
            }}
          >
            "Emotion inputs (Member 1 MER integration pending) and visual preview (Member 2 final visualization & Member 3 transition integration pending) are simulated for progress demonstration. Real Member 4 LinUCB bandit learning and PostgreSQL persistence are live."
          </p>
        </div>

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
          <span>Viva Demo Script</span>
        </button>
      </header>

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
        />

        {/* Two-Column Main Stage: Controls & Preview */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {/* Left Column: Emotion Input & Recommendation Action */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <EmotionControl
              valence={valence}
              arousal={arousal}
              onValenceChange={setValence}
              onArousalChange={setArousal}
              disabled={isLoadingRec}
            />

            <RecommendationCard
              recommendation={recommendation}
              isLoading={isLoadingRec}
              onGetRecommendation={handleGetRecommendation}
              valence={valence}
              arousal={arousal}
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
            onRefresh={() => fetchSingleUserState(currentUserId).then(setActiveUserState)}
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
