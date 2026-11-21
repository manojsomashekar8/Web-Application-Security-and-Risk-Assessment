import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { loadConfig } from "./api.js";
import Login from "./pages/Login.jsx";
import Targets from "./pages/Targets.jsx";
import NewTarget from "./pages/NewTarget.jsx";
import TargetDetail from "./pages/TargetDetail.jsx";
import Findings from "./pages/Findings.jsx";

export default function App() {
  const [mode, setMode] = useState(null);
  const [error, setError] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    loadConfig().then((c) => setMode(c.auth_mode)).catch((e) => setError(e.message));
  }, []);

  let body;
  if (error) body = <p className="error">{error}</p>;
  else if (!mode) body = <p className="muted">Starting...</p>;
  else if (mode === "basic" && !loggedIn) body = <Login onLogin={() => setLoggedIn(true)} />;
  else body = (
    <Routes>
      <Route path="/" element={<Targets />} />
      <Route path="/targets/new" element={<NewTarget />} />
      <Route path="/targets/:id" element={<TargetDetail />} />
      <Route path="/scans/:id" element={<Findings />} />
      <Route path="*" element={<p className="muted">Page not found. <Link to="/">Back to targets</Link></p>} />
    </Routes>
  );

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">WASRA</Link>
        <span className="tagline">Web application risk assessment</span>
      </header>
      <main className="container">{body}</main>
    </>
  );
}
