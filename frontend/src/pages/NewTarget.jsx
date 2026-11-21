import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, CONTEXT, LEVELS } from "../api.js";

export default function NewTarget() {
  const nav = useNavigate();
  const [allowed, setAllowed] = useState([]);
  const [form, setForm] = useState({
    name: "", url: "", criticality: "Medium", data_sensitivity: "Medium",
    internet_exposure: "Medium", business_impact: "Medium",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api("/allowed-targets").then((list) => {
      setAllowed(list);
      setForm((f) => ({ ...f, url: f.url || list[0] || "" }));
    }).catch((e) => setError(e.message));
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const { id } = await api("/targets", { method: "POST", body: JSON.stringify(form) });
      nav(`/targets/${id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="narrow">
      <h1>Add target</h1>
      <p className="muted">Only sites on the allowlist (docs/TARGETS.md) can be scanned.</p>
      <form onSubmit={submit} className="form">
        <label>Name<input required value={form.name} onChange={set("name")} placeholder="e.g. Customer portal" /></label>
        <label>Website
          <select value={form.url} onChange={set("url")}>
            {allowed.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </label>
        {CONTEXT.map(([key, label, hint]) => (
          <label key={key}>
            <span>{label}</span>
            <small className="muted">{hint}</small>
            <select value={form[key]} onChange={set(key)}>
              {LEVELS.map((l) => <option key={l}>{l}</option>)}
            </select>
          </label>
        ))}
        {error && <p className="error">{error}</p>}
        <button className="button" disabled={saving}>{saving ? "Saving..." : "Save target"}</button>
      </form>
    </section>
  );
}
