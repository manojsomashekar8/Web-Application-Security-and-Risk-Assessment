import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { StatusBadge } from "../components.jsx";
import Status from "./Status.jsx";

export default function Targets() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/targets")
      .then(async (targets) => {
        const scans = await Promise.all(targets.map((t) => api(`/targets/${t.id}/latest-scan`).catch(() => null)));
        setRows(targets.map((t, i) => ({ ...t, scan: scans[i] })));
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <section>
      <div className="row between">
        <h1>Targets</h1>
        <Link className="button" to="/targets/new">Add target</Link>
      </div>
      <Status />
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p className="muted">Loading targets...</p>}
      {rows && rows.length === 0 && <p className="muted">No targets yet. Add one to start a scan.</p>}
      {rows && rows.length > 0 && (
        <div className="cards">
          {rows.map((t) => (
            <Link key={t.id} to={`/targets/${t.id}`} className="card">
              <div className="row between">
                <strong>{t.name}</strong>
                <StatusBadge status={t.scan?.status} />
              </div>
              <div className="muted small mono">{t.url}</div>
              <div className="small">Criticality {t.criticality} · Exposure {t.internet_exposure}</div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
