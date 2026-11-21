import { useState } from "react";
import { api, clearCredentials, setCredentials } from "../api.js";

export default function Login({ onLogin }) {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setCredentials(user, pass);
    try {
      await api("/targets"); // checks the credentials against the server
      onLogin();
    } catch (err) {
      clearCredentials();
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="narrow">
      <h1>Log in</h1>
      <p className="muted">This server requires a login (AUTH_MODE=basic).</p>
      <form onSubmit={submit} className="form">
        <label>Username<input required autoComplete="username" value={user} onChange={(e) => setUser(e.target.value)} /></label>
        <label>Password<input required type="password" autoComplete="current-password" value={pass} onChange={(e) => setPass(e.target.value)} /></label>
        {error && <p className="error">{error}</p>}
        <button className="button" disabled={busy}>{busy ? "Checking..." : "Log in"}</button>
      </form>
    </section>
  );
}
