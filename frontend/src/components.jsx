// Small shared pieces. Missing values are shown as "n/a", never as 0.
export function StatusBadge({ status }) {
  const label = status || "never scanned";
  return <span className={`badge ${status || "none"}`}>{label}</span>;
}

export function Value({ v, digits = 2 }) {
  if (v === null || v === undefined || v === "") return <span className="muted">n/a</span>;
  return typeof v === "number" ? v.toFixed(digits) : v;
}

export function BandBadge({ band }) {
  return <span className={`band ${band.toLowerCase()}`}>{band}</span>;
}

export function ClassBadge({ value }) {
  return <span className={`class ${value}`}>{value}</span>;
}

// Why a CVE-based value is missing, shown as a tooltip on the "n/a" (provenance status from the backend).
export const NA_REASON = {
  no_cve: "No CVE is mapped to this ZAP alert (configs/cve_map.json), so CVSS, EPSS and KEV do not apply.",
  not_in_feed: "The mapped CVE is not in the saved feed snapshot.",
  unavailable: "The feed file was missing or unreadable, so this value could not be loaded.",
};

export function naTitle(provenance, field) {
  const status = provenance?.[field]?.status;
  return NA_REASON[status] || "Not available for this finding.";
}
