import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, CONTEXT } from "../api.js";
import { StatusBadge } from "../components.jsx";

// Turn the form into the request the server validates (src/scanprofile.py). Lists are split here, not guessed later.
function customBody(c) {
  const lines = (s) => s.split("\n").map((x) => x.trim()).filter(Boolean);
  const ids = c.disable_rules.split(",").map((x) => x.trim()).filter(Boolean);
  return { ...c, exclude_urls: lines(c.exclude_urls), disable_rules: ids };
}

export default function TargetDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [target, setTarget] = useState(null);
  const [scan, setScan] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [profile, setProfile] = useState("deep");
  const [custom, setCustom] = useState({ spider: "traditional", active_scan: true, attack_strength: "DEFAULT", alert_threshold: "DEFAULT", threads_per_host: 24, delay_ms: 0, max_scan_minutes: 60, max_rule_minutes: 5, exclude_urls: "", disable_rules: "" });

  useEffect(() => {
    api("/targets").then((list) => setTarget(list.find((t) => String(t.id) === id) || null)).catch((e) => setError(e.message));
    api(`/targets/${id}/latest-scan`).then(setScan).catch(() => {});
  }, [id]);

  async function startScan() {
    setBusy(true);
    setError("");
    try {
      const body = profile === "custom" ? { profile, custom: customBody(custom) } : { profile };
      const { scan_id } = await api(`/targets/${id}/scan`, { method: "POST", body: JSON.stringify(body) });
      nav(`/scans/${scan_id}`);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!target) return <p className="muted">Loading...</p>;

  return (
    <section>
      <h1>{target.name}</h1>
      <p className="mono muted">{target.url}</p>
      <div className="card">
        <h3>Business context</h3>
        <dl className="grid-dl">
          {CONTEXT.map(([key, label]) => (
            <div key={key} className="dl-row"><dt>{label}</dt><dd>{target[key]}</dd></div>
          ))}
        </dl>
      </div>
      <div className="card">
        <h3>Scan</h3>
        <p>Latest scan: <StatusBadge status={scan?.status} /> {scan?.error && <span className="error">{scan.error}</span>}</p>
        <label>Profile
          <select value={profile} onChange={(e) => setProfile(e.target.value)}>
            <option value="quick">quick: a few minutes, no attacks</option>
            <option value="standard">standard: attacks at Low strength, time limits</option>
            <option value="deep">deep: the reference scan, no limits</option>
            <option value="custom">custom</option>
          </select>
        </label>
        {profile === "custom" && (
          <div className="grid-form">
            <label>Spider<select value={custom.spider} onChange={(e) => setCustom({ ...custom, spider: e.target.value })}><option value="traditional">traditional</option><option value="ajax">AJAX</option><option value="none">none</option></select></label>
            <label>Active scan<select value={String(custom.active_scan)} onChange={(e) => setCustom({ ...custom, active_scan: e.target.value === "true" })}><option value="true">on</option><option value="false">off</option></select></label>
            <label>Attack strength<select value={custom.attack_strength} onChange={(e) => setCustom({ ...custom, attack_strength: e.target.value })}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>DEFAULT</option></select></label>
            <label>Alert threshold<select value={custom.alert_threshold} onChange={(e) => setCustom({ ...custom, alert_threshold: e.target.value })}><option>OFF</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>DEFAULT</option></select></label>
            <label>Threads per host (1-24)<input type="number" min="1" max="24" value={custom.threads_per_host} onChange={(e) => setCustom({ ...custom, threads_per_host: Number(e.target.value) })} /></label>
            <label>Delay between requests, ms (0-2000)<input type="number" min="0" max="2000" value={custom.delay_ms} onChange={(e) => setCustom({ ...custom, delay_ms: Number(e.target.value) })} /></label>
            <label>Max scan minutes (1-240)<input type="number" min="1" max="240" value={custom.max_scan_minutes} onChange={(e) => setCustom({ ...custom, max_scan_minutes: Number(e.target.value) })} /></label>
            <label>Max rule minutes (1-60)<input type="number" min="1" max="60" value={custom.max_rule_minutes} onChange={(e) => setCustom({ ...custom, max_rule_minutes: Number(e.target.value) })} /></label>
            <label>Excluded URL patterns (one per line)<textarea value={custom.exclude_urls} onChange={(e) => setCustom({ ...custom, exclude_urls: e.target.value })} /></label>
            <label>Rule ids to disable (comma-separated)<input value={custom.disable_rules} onChange={(e) => setCustom({ ...custom, disable_rules: e.target.value })} /></label>
          </div>
        )}
        <div className="row">
          <button className="button" onClick={startScan} disabled={busy}>{busy ? "Starting..." : "Start scan"}</button>
          {scan && <Link className="button ghost" to={`/scans/${scan.id}`}>Open latest results</Link>}
        </div>
        <p className="small muted">A scan can take a long time. Only one scan runs at a time.</p>
      </div>
    </section>
  );
}
