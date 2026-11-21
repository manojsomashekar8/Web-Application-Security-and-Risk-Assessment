import { useEffect, useState } from "react";
import { api } from "../api.js";

// Status panel: Postgres, ZAP and feed freshness. Each line shows its own error if a check fails.
export default function Status() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/health").then(setHealth).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card"><h3>System status</h3><p className="error">{error}</p></div>;
  if (!health) return <div className="card"><h3>System status</h3><p className="muted">Checking...</p></div>;

  const line = (label, ok, detail) => (
    <div className="dl-row">
      <dt>{label}</dt>
      <dd><span className={`dot ${ok ? "ok" : "bad"}`} /> {detail}</dd>
    </div>
  );
  const f = health.feeds;
  return (
    <div className="card">
      <div className="row between">
        <h3>System status</h3>
        <span className={`badge ${health.status === "ok" ? "done" : "failed"}`}>{health.status}</span>
      </div>
      <div className="grid-dl">
        {line("Database (Postgres)", health.postgres.ok, health.postgres.ok ? "reachable" : health.postgres.error)}
        {line("Scanner (ZAP)", health.zap.ok, health.zap.ok ? `version ${health.zap.version}` : health.zap.error)}
        {line("Feed snapshot", f.status === "fresh",
          f.snapshot_date ? `${f.snapshot_date} (${f.age_days} days old, ${f.status})` : `${f.status}: ${f.error || ""}`)}
      </div>
    </div>
  );
}
