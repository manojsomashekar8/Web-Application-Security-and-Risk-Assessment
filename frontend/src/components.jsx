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
