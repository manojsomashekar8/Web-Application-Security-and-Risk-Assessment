// JSON API helper. In basic mode the user logs in once; the credentials are kept in memory only
// (never in localStorage) and sent as an Authorization header on every request.
let authHeader = null;

export function setCredentials(user, pass) {
  authHeader = "Basic " + btoa(`${user}:${pass}`);
}

export function clearCredentials() {
  authHeader = null;
}

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(authHeader ? { Authorization: authHeader } : {}) };
  const res = await fetch(`/api${path}`, { credentials: "same-origin", ...options, headers: { ...headers, ...(options.headers || {}) } });
  if (res.status === 401) throw new Error("Wrong username or password, or login required.");
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = JSON.stringify((await res.json()).detail); } catch { /* keep statusText */ }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

export async function loadConfig() {
  const res = await fetch("/api/config");
  if (!res.ok) throw new Error(`Cannot read server config (${res.status})`);
  return res.json();
}

export const LEVELS = ["Low", "Medium", "High"];
export const CONTEXT = [
  ["criticality", "Criticality", "How important is the app to the business?"],
  ["data_sensitivity", "Data sensitivity", "What data does it hold?"],
  ["internet_exposure", "Internet exposure", "Can anyone on the internet reach it?"],
  ["business_impact", "Business impact", "Impact if it is compromised."],
];

// Same thresholds as src/scoring/score.py band()
export function band(score) {
  return score >= 60 ? "High" : score >= 30 ? "Medium" : "Low";
}
