import { Link, Route, Routes } from "react-router-dom";
import Targets from "./pages/Targets.jsx";
import NewTarget from "./pages/NewTarget.jsx";
import TargetDetail from "./pages/TargetDetail.jsx";
import Findings from "./pages/Findings.jsx";

export default function App() {
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">WASRA</Link>
        <span className="tagline">Web application risk assessment</span>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<Targets />} />
          <Route path="/targets/new" element={<NewTarget />} />
          <Route path="/targets/:id" element={<TargetDetail />} />
          <Route path="/scans/:id" element={<Findings />} />
          <Route path="*" element={<p className="muted">Page not found. <Link to="/">Back to targets</Link></p>} />
        </Routes>
      </main>
    </>
  );
}
