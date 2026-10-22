/**
 * API client for Member 4: Adaptive Personalization & User Analytics.
 * Connects to FastAPI backend at VITE_API_BASE_URL (defaults to http://localhost:8000).
 */

import type {
  MERTier3Event,
  RecommendationResponse,
  FeedbackEvent,
  FeedbackResponse,
  UserPersonalizationStateData,
} from "../types/personalization";

const getBaseUrl = (): string => {
  const envUrl = (import.meta as any).env?.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === "string") {
    return envUrl.replace(/\/+$/, "");
  }
  return "http://localhost:8000";
};

export class PersonalizationApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "PersonalizationApiError";
    this.status = status;
    this.details = details;
  }
}

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${path}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    throw new PersonalizationApiError(
      `Cannot connect to backend server at ${baseUrl}. Ensure FastAPI is running.`,
      0,
      err
    );
  }

  let data: any = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const detailMsg =
      data && typeof data === "object" && data.detail
        ? typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail)
        : `Request failed with status ${response.status}`;
    throw new PersonalizationApiError(detailMsg, response.status, data);
  }

  return data as T;
}

/**
 * Request next visual preset recommendation from real LinUCB / Cold-Start backend.
 * Optionally passes Member 2 candidate_visual_ids and default_visual_id.
 */
export async function getRecommendation(
  userId: string,
  tier3Event: MERTier3Event,
  candidateVisualIds?: string[],
  defaultVisualId?: string
): Promise<RecommendationResponse> {
  const payload: Record<string, unknown> = {
    user_id: userId,
    tier3_event: tier3Event,
  };
  if (candidateVisualIds && candidateVisualIds.length > 0) {
    payload.candidate_visual_ids = candidateVisualIds;
  }
  if (defaultVisualId) {
    payload.default_visual_id = defaultVisualId;
  }
  return requestJson<RecommendationResponse>("/api/personalization/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Submit user feedback event to update bandit model (LinUCB learning).
 */
export async function submitFeedback(
  userId: string,
  feedbackEvent: FeedbackEvent
): Promise<FeedbackResponse> {
  return requestJson<FeedbackResponse>("/api/personalization/feedback", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      feedback_event: feedbackEvent,
    }),
  });
}

/**
 * Fetch real user personalization state and analytics from PostgreSQL persistence.
 */
export async function getUserState(
  userId: string
): Promise<UserPersonalizationStateData | null> {
  try {
    return await requestJson<UserPersonalizationStateData>(
      `/api/personalization/users/${encodeURIComponent(userId)}/state`
    );
  } catch (err: any) {
    if (err instanceof PersonalizationApiError && err.status === 404) {
      return null; // User hasn't interacted yet
    }
    throw err;
  }
}

/**
 * Check backend connection status.
 */
export async function checkBackendHealth(): Promise<{ online: boolean; message: string }> {
  try {
    const baseUrl = getBaseUrl();
    const res = await fetch(`${baseUrl}/health`, { method: "GET" });
    if (res.ok) {
      return { online: true, message: `Connected to FastAPI (${baseUrl})` };
    }
    return { online: false, message: `Server returned HTTP ${res.status}` };
  } catch (err: any) {
    return {
      online: false,
      message: `Offline (${err?.message || "connection refused"})`,
    };
  }
}

/**
 * Reset demo integration users back to cold-start baseline (clears database records & runtime cache).
 */
export async function resetDemoUsers(
  userIds?: string[]
): Promise<{ status: string; message: string; reset_users: string[] }> {
  return requestJson<{ status: string; message: string; reset_users: string[] }>(
    "/api/personalization/demo/reset",
    {
      method: "POST",
      body: JSON.stringify(userIds && userIds.length > 0 ? { user_ids: userIds } : {}),
    }
  );
}

