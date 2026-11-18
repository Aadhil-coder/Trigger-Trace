// Every call to the backend goes through this file.
// The Vite dev server forwards /api to the Flask backend (see vite.config.js).

const BASE = "/api";
const PROFILE_KEY = "tt_profile_id";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getProfileId() {
  const value = Number(localStorage.getItem(PROFILE_KEY));
  return value > 0 ? value : 1;
}

export function setProfileId(id) {
  localStorage.setItem(PROFILE_KEY, String(id));
}

async function request(path, { method = "GET", body } = {}) {
  const init = { method };
  if (body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.error) message = data.error;
    } catch {
      // the response was not JSON; keep the generic message
    }
    throw new ApiError(message, res.status);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),

  listProfiles: () => request("/profiles"),
  createProfile: (data) => request("/profiles", { method: "POST", body: data }),
  updateProfile: (id, data) => request(`/profiles/${id}`, { method: "PATCH", body: data }),
  deleteProfileData: (id) => request(`/profiles/${id}/data`, { method: "DELETE" }),
  deleteProfile: (id) => request(`/profiles/${id}`, { method: "DELETE" }),

  createAttack: (data) => request("/attacks", { method: "POST", body: data }),
  updateAttack: (id, data) => request(`/attacks/${id}`, { method: "PATCH", body: data }),
  listAttacks: (profileId) => request(`/attacks?profile_id=${profileId}`),

  saveCheckin: (data) => request("/checkins", { method: "POST", body: data }),
  listCheckins: (profileId, { from, to } = {}) => {
    const query = new URLSearchParams({ profile_id: profileId });
    if (from) query.set("from", from);
    if (to) query.set("to", to);
    return request(`/checkins?${query}`);
  },

  patterns: (profileId) => request(`/patterns?profile_id=${profileId}`),

  downloadReport: async (profileId) => {
    const res = await fetch(`${BASE}/report?profile_id=${profileId}`);
    if (!res.ok) throw new ApiError("Could not create the summary. Try again.", res.status);

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `triggertrace_summary_profile_${profileId}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
