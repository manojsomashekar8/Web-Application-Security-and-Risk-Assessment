// Thin wrapper over the JSON API. The browser sends the Basic-auth login it already holds.
export async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 401) throw new Error("Login required: reload the page and enter your WASRA username and password.");
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = JSON.stringify((await res.json()).detail); } catch { /* keep statusText */ }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.status === 204 ? null : res.json();
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
