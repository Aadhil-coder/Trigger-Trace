import { useEffect, useState } from "react";
import { api } from "../api.js";

function fmt(iso) {
  return iso.replace("T", " ").slice(0, 16);
}

export default function Summary({ profileId }) {
  const [attacks, setAttacks] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | working | done | error
  const [error, setError] = useState("");

  useEffect(() => {
    api.listAttacks(profileId)
      .then(setAttacks)
      .catch(() => setAttacks([]));
    api.patterns(profileId)
      .then(setPatterns)
      .catch(() => setPatterns(null));
  }, [profileId]);

  async function download() {
    setStatus("working");
    setError("");
    try {
      await api.downloadReport(profileId);
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setError(err.message);
    }
  }

  const recent = attacks ? attacks.slice(0, 5) : [];

  return (
    <>
      <h1>Doctor summary</h1>
      <p className="muted">
        A one-page PDF with your attack dates, severity and possible patterns. It is not a diagnosis.
      </p>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Overview</h2>
        <p>Attacks logged: <strong>{attacks ? attacks.length : "..."}</strong></p>

        {patterns && patterns.status === "ok" ? (
          <p>
            Possible patterns are ready. The PDF includes odds ratios and confidence notes.
          </p>
        ) : (
          <p className="muted">
            {patterns ? patterns.message : "Patterns are not available right now."}
          </p>
        )}
      </div>

      {recent.length > 0 && (
        <>
          <h2>Most recent attacks</h2>
          <ul className="list">
            {recent.map((a) => (
              <li key={a.id}>
                <strong>{fmt(a.attacked_at)}</strong>
                <div className="muted">
                  Severity: {a.severity || "not recorded"}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
      {status === "done" && <p className="ok-text">PDF downloaded.</p>}

      <button
        className="btn btn-primary btn-block"
        style={{ marginTop: 16 }}
        onClick={download}
        disabled={status === "working"}
      >
        {status === "working" ? "Creating PDF..." : "Download PDF"}
      </button>
      <p className="muted" style={{ marginTop: 8 }}>
        Creating the PDF needs an internet connection to the backend.
      </p>
    </>
  );
}
