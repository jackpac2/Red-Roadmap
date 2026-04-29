const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep the fallback message.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  getMissions: () => request("/api/missions"),
  createMission: (payload) => request("/api/missions", { method: "POST", body: JSON.stringify(payload) }),
  updateMission: (id, payload) => request(`/api/missions/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  patchMission: (id, payload) => request(`/api/missions/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  updateReminder: (id, reminderAt) =>
    request(`/api/missions/${id}`, { method: "PATCH", body: JSON.stringify({ reminder_at: reminderAt }) }),
  clearReminder: (id) =>
    request(`/api/missions/${id}`, { method: "PATCH", body: JSON.stringify({ clear_reminder: true }) }),
  snoozeMission: (id, minutes = 10) =>
    request(`/api/missions/${id}/snooze`, { method: "POST", body: JSON.stringify({ minutes }) }),
  deleteMission: (id) => request(`/api/missions/${id}`, { method: "DELETE" }),
  deleteAllMissions: () => request("/api/missions", { method: "DELETE" }),
  completeMission: (id, completed = true) =>
    request(`/api/missions/${id}/complete`, { method: "POST", body: JSON.stringify({ completed }) }),
  startMission: (id) => request(`/api/missions/${id}/start`, { method: "POST" }),
  addStep: (missionId, title) =>
    request(`/api/missions/${missionId}/steps`, { method: "POST", body: JSON.stringify({ title }) }),
  updateStep: (id, title) => request(`/api/steps/${id}`, { method: "PUT", body: JSON.stringify({ title }) }),
  deleteStep: (id) => request(`/api/steps/${id}`, { method: "DELETE" }),
  completeStep: (id, completed) =>
    request(`/api/steps/${id}/complete`, { method: "POST", body: JSON.stringify({ completed }) }),
  getStats: () => request("/api/dashboard/stats"),
  getProgress: () => request("/api/dashboard/progress"),
  getExecutionScore: () => request("/api/dashboard/execution-score"),
  getTimeline: () => request("/api/roadmap/timeline")
};
