import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, CONTEXT } from "../api.js";
import { StatusBadge } from "../components.jsx";

export default function TargetDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [target, setTarget] = useState(null);
  const [scan, setScan] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/targets").then((list) => setTarget(list.find((t) => String(t.id) === id) || null)).catch((e) => setError(e.message));
    api(`/targets/${id}/latest-scan`).then(setScan).catch(() => {});
  }, [id]);

  async function startScan() {
    setBusy(true);
    setError("");
    try {
      const { scan_id } = await api(`/targets/${id}/scan`, { method: "POST" });
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
        <div className="row">
          <button className="button" onClick={startScan} disabled={busy}>{busy ? "Starting..." : "Start scan"}</button>
          {scan && <Link className="button ghost" to={`/scans/${scan.id}`}>Open latest results</Link>}
        </div>
        <p className="small muted">A scan can take a long time. Only one scan runs at a time.</p>
      </div>
    </section>
  );
}
