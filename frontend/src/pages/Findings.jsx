import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, band, download } from "../api.js";
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
  const [sort, setSort] = useState({ key: "risk", dir: "desc" });

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

  const shown = useMemo(() => {
    const kept = (rows || []).filter((r) =>
      (cls === "all" || r.classification === cls) && (bandFilter === "all" || band(r.risk) === bandFilter));
    // Ties keep the stored deterministic order (rank_risk ascending), so the sort is stable across reloads.
    const value = {
      rank: (r) => r.rank_risk, finding: (r) => r.type, class: (r) => r.classification, risk: (r) => r.risk,
      band: (r) => r.risk, zap_risk: (r) => ["Informational", "Low", "Medium", "High"].indexOf(r.zap_risk),
      confidence: (r) => ["False Positive", "Low", "Medium", "High"].indexOf(r.zap_confidence),
      cvss: (r) => r.cvss, epss: (r) => r.epss, kev: (r) => (r.kev === null ? -1 : r.kev ? 1 : 0),
      count: (r) => r.occurrences,
    }[sort.key];
    const dir = sort.dir === "asc" ? 1 : -1;
    return kept.sort((a, b) => {
      const x = value(a), y = value(b);
      const xn = x === null || x === undefined, yn = y === null || y === undefined;
      if (xn !== yn) return xn ? 1 : -1; // n/a always sorts last
      if (x !== y) return (x < y ? -1 : 1) * dir;
      return a.rank_risk - b.rank_risk;
    });
  }, [rows, cls, bandFilter, sort]);

  const sortBy = (key) => setSort((s) => ({ key, dir: s.key === key && s.dir === "desc" ? "asc" : "desc" }));
  const arrow = (key) => (sort.key === key ? (sort.dir === "desc" ? " ▼" : " ▲") : "");

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
        <div className="row wrap">
          <button className="button ghost" onClick={rescore} disabled={busy}>{busy ? "Re-scoring..." : "Re-score"}</button>
          <button className="button ghost" onClick={() => download(`/scans/${id}/report.html`, `scan-${id}.html`).catch((e) => setError(e.message))}>Full report (HTML)</button>
          <button className="button ghost" onClick={() => download(`/scans/${id}/report.json`, `scan-${id}.json`).catch((e) => setError(e.message))}>Full report (JSON)</button>
          <button className="button ghost" onClick={() => download(`/scans/${id}/findings.csv`, `scan-${id}-findings.csv`).catch((e) => setError(e.message))}>Findings (CSV)</button>
        </div>
      </div>

      <ScanSettings scan={scan} />

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
              <th className="sortable" onClick={() => sortBy("rank")}>Rank{arrow("rank")}</th> <th className="sortable" onClick={() => sortBy("finding")}>Finding{arrow("finding")}</th> <th className="sortable" onClick={() => sortBy("class")}>Class{arrow("class")}</th> <th className="sortable" onClick={() => sortBy("risk")}>Risk{arrow("risk")}</th> <th className="sortable" onClick={() => sortBy("band")}>Band{arrow("band")}</th> <th className="sortable" onClick={() => sortBy("zap_risk")}>ZAP risk{arrow("zap_risk")}</th> <th className="sortable" onClick={() => sortBy("confidence")}>Confidence{arrow("confidence")}</th> <th className="sortable" onClick={() => sortBy("cvss")}>CVSS (from CVE){arrow("cvss")}</th> <th className="sortable" onClick={() => sortBy("epss")}>EPSS (from CVE){arrow("epss")}</th> <th className="sortable" onClick={() => sortBy("kev")}>KEV (from CVE){arrow("kev")}</th> <th className="sortable" onClick={() => sortBy("count")}>Count{arrow("count")}</th>
              <th>Report</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => (
              <FindingRow key={r.id} r={r} isOpen={open === r.id} onToggle={() => setOpen(open === r.id ? null : r.id)}
                onError={setError} />
            ))}
            {shown.length === 0 && <tr><td colSpan="12" className="muted">No findings match these filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FindingRow({ r, isOpen, onToggle, onError }) {
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
        <td onClick={(e) => e.stopPropagation()}>
          <button className="linkbtn" onClick={() => download(`/findings/${r.id}/report.html`, `finding-${r.id}.html`).catch((e) => onError(e.message))}>HTML</button>
          {" · "}
          <button className="linkbtn" onClick={() => download(`/findings/${r.id}/report.json`, `finding-${r.id}.json`).catch((e) => onError(e.message))}>JSON</button>
        </td>
      </tr>
      {isOpen && (
        <tr className="detail">
          <td colSpan="12">
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

// The exact settings this scan used, and how long each stage took (stored with the scan).
function ScanSettings({ scan }) {
  const s = scan.settings;
  if (!s) return <p className="small muted">Settings: not recorded (this scan ran before profiles existed).</p>;
  const stages = scan.stage_seconds || {};
  return (
    <div className="card">
      <h3>Settings used: profile {s.profile}</h3>
      <p className="small muted">{s.description}</p>
      <div className="grid-dl">
        {Object.entries(s).filter(([k]) => !["profile", "description"].includes(k)).map(([k, v]) => (
          <div key={k} className="dl-row"><dt>{k}</dt><dd>{Array.isArray(v) ? (v.length ? v.join(", ") : "none") : String(v ?? "default")}</dd></div>
        ))}
      </div>
      <h3 style={{ marginTop: "0.8rem" }}>Stage durations</h3>
      <div className="grid-dl">
        {Object.entries(stages).map(([k, v]) => (
          <div key={k} className="dl-row"><dt>{k}</dt><dd>{v} s</dd></div>
        ))}
      </div>
    </div>
  );
}
