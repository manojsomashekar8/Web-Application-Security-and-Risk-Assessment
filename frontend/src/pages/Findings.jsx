import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, band } from "../api.js";
import { BandBadge, ClassBadge, StatusBadge, Value, naTitle } from "../components.jsx";

const CLASSES = ["vulnerability", "potential", "informational", "excluded"];

export default function Findings() {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [cls, setCls] = useState("all");
  const [bandFilter, setBandFilter] = useState("all");
  const [open, setOpen] = useState(null);
  const [busy, setBusy] = useState(false);

  // Recompute from the stored raw alerts with the target's current context. No new scan is started.
  async function rescore() {
    setBusy(true);
    setError("");
    try {
      await api(`/scans/${id}/rescore`, { method: "POST" });
      setRows(await api(`/scans/${id}/findings`));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  // Poll the scan until it finishes, then load its findings once.
  useEffect(() => {
    let timer;
    const check = () => api(`/scans/${id}`).then((s) => {
      setScan(s);
      if (s.status === "running") timer = setTimeout(check, 5000);
      else if (s.status === "done") api(`/scans/${id}/findings`).then(setRows).catch((e) => setError(e.message));
    }).catch((e) => setError(e.message));
    check();
    return () => clearTimeout(timer);
  }, [id]);

  const summary = useMemo(() => {
    if (!rows) return null;
    const count = (f) => rows.filter(f).length;
    return {
      raw: rows.reduce((n, r) => n + r.occurrences, 0),
      unique: rows.length,
      High: count((r) => band(r.risk) === "High"),
      Medium: count((r) => band(r.risk) === "Medium"),
      Low: count((r) => band(r.risk) === "Low"),
      byClass: Object.fromEntries(CLASSES.map((c) => [c, count((r) => r.classification === c)])),
    };
  }, [rows]);

  const shown = useMemo(() => (rows || []).filter((r) =>
    (cls === "all" || r.classification === cls) && (bandFilter === "all" || band(r.risk) === bandFilter)
  ), [rows, cls, bandFilter]);

  if (error) return <p className="error">{error}</p>;
  if (!scan) return <p className="muted">Loading scan...</p>;
  if (scan.status !== "done") {
    return (
      <section>
        <h1>Scan #{id}</h1>
        <p>Status: <StatusBadge status={scan.status} /></p>
        {scan.status === "running" && <p className="muted">Scanning. This page updates automatically.</p>}
        {scan.error && <p className="error">{scan.error}</p>}
        <Link to="/">Back to targets</Link>
      </section>
    );
  }

  if (!rows) return <p className="muted">Loading results...</p>;

  return (
    <section>
      <div className="row between">
        <h1>Scan #{id} results</h1>
        <div className="row">
          <button className="button ghost" onClick={rescore} disabled={busy}>{busy ? "Re-scoring..." : "Re-score"}</button>
          <a className="button ghost" href={`/api/scans/${id}/report.json`}>Download JSON report</a>
        </div>
      </div>

      <div className="cards stats">
        <Stat label="Raw alerts" value={summary.raw} hint="Every alert the scanner raised" />
        <Stat label="Unique findings" value={summary.unique} hint="Repeats on the same URL and parameter merged" />
        <Stat label="High risk" value={summary.High} tone="high" />
        <Stat label="Medium risk" value={summary.Medium} tone="medium" />
        <Stat label="Low risk" value={summary.Low} tone="low" />
      </div>

      <div className="card">
        <h3>By classification</h3>
        <p className="small muted">Scanner alerts are not proven exploits. Informational items are notes, not vulnerabilities.</p>
        <div className="row wrap">
          {CLASSES.map((c) => (
            <button key={c} className={`pill ${cls === c ? "active" : ""}`} onClick={() => setCls(cls === c ? "all" : c)}>
              <ClassBadge value={c} /> {summary.byClass[c]}
            </button>
          ))}
        </div>
      </div>

      <div className="row wrap filters">
        <label>Class
          <select value={cls} onChange={(e) => setCls(e.target.value)}>
            <option value="all">All</option>
            {CLASSES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>Risk band
          <select value={bandFilter} onChange={(e) => setBandFilter(e.target.value)}>
            <option value="all">All</option><option>High</option><option>Medium</option><option>Low</option>
          </select>
        </label>
        <span className="muted small">Showing {shown.length} of {rows.length}</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rank</th><th>Finding</th><th>Class</th><th>Risk</th><th>Band</th>
              <th>ZAP risk</th><th>Confidence</th><th>CVSS (from CVE)</th><th>EPSS (from CVE)</th><th>KEV (from CVE)</th><th>Count</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => (
              <FindingRow key={r.id} r={r} isOpen={open === r.id} onToggle={() => setOpen(open === r.id ? null : r.id)} />
            ))}
            {shown.length === 0 && <tr><td colSpan="11" className="muted">No findings match these filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FindingRow({ r, isOpen, onToggle }) {
  const factors = typeof r.factors === "string" ? JSON.parse(r.factors) : r.factors;
  return (
    <>
      <tr className="clickable" onClick={onToggle}>
        <td>{r.rank_risk}</td>
        <td><strong>{r.type}</strong><div className="muted small mono">{r.url}</div></td>
        <td><ClassBadge value={r.classification} /></td>
        <td><Value v={r.risk} digits={1} /></td>
        <td><BandBadge band={band(r.risk)} /></td>
        <td>{r.zap_risk}</td>
        <td>{r.zap_confidence}</td>
        <td title={naTitle(r.provenance, "cvss")}><Value v={r.cvss} digits={1} /></td>
        <td title={naTitle(r.provenance, "epss")}><Value v={r.epss} digits={3} /></td>
        <td title={naTitle(r.provenance, "kev")}>{r.kev === null || r.kev === undefined ? <span className="muted">n/a</span> : r.kev ? "yes" : "no"}</td>
        <td>{r.occurrences}</td>
      </tr>
      {isOpen && (
        <tr className="detail">
          <td colSpan="11">
            <p><strong>Why this score:</strong> {r.explanation}</p>
            <div className="grid-dl">
              <div className="dl-row"><dt>Severity (S)</dt><dd><Value v={factors.S} /></dd></div>
              <div className="dl-row"><dt>Exploitability (E)</dt><dd><Value v={factors.E} /></dd></div>
              <div className="dl-row"><dt>Internet exposure</dt><dd><Value v={factors.exposure} /></dd></div>
              <div className="dl-row"><dt>Impact (I)</dt><dd><Value v={factors.I} /></dd></div>
              <div className="dl-row"><dt>Likelihood (L)</dt><dd><Value v={factors.L} /></dd></div>
              <div className="dl-row"><dt>Severity used (S)</dt><dd>{Number(factors.S).toFixed(2)} ({r.cvss != null ? `CVSS ${r.cvss}` : `ZAP risk ${r.zap_risk}`})</dd></div>
              <div className="dl-row"><dt>CVE</dt><dd title={r.cve ? "" : naTitle(r.provenance, "cvss")}>{r.cve || "n/a"}</dd></div>
              <div className="dl-row"><dt>CWE</dt><dd>{r.cwe || "n/a"}</dd></div>
              <div className="dl-row"><dt>OWASP</dt><dd>{r.owasp || "n/a"}</dd></div>
              <div className="dl-row"><dt>Rank: CVSS only</dt><dd>{r.rank_cvss_only}</dd></div>
              <div className="dl-row"><dt>Rank: ZAP risk only</dt><dd>{r.rank_zap_risk_only}</dd></div>
              <div className="dl-row"><dt>Rank: weighted sum</dt><dd>{r.rank_weighted_sum}</dd></div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function Stat({ label, value, hint, tone }) {
  return (
    <div className={`card stat ${tone || ""}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="small muted">{hint}</div>}
    </div>
  );
}
