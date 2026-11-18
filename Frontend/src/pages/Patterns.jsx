import { useEffect, useState } from "react";
import { api } from "../api.js";

function Disclaimer({ text }) {
  return (
    <div className="warn-box" style={{ marginTop: 16 }}>
      {text}
    </div>
  );
}

export default function Patterns({ profileId }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, [profileId]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setResult(await api.patterns(profileId));
    } catch (err) {
      setError(`Patterns need a connection to the backend. (${err.message})`);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <p className="muted">Working out your patterns...</p>;

  if (error) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
        <button className="btn btn-block" onClick={load}>Try again</button>
      </div>
    );
  }

  if (!result) return null;

  if (result.status !== "ok") {
    return (
      <>
        <h1>Patterns</h1>
        <div className="card">
          <p>{result.message}</p>
          <p className="muted">
            Attack days logged: {result.n_attack_days} · Check-in days: {result.n_checkin_days}
          </p>
        </div>
        <Disclaimer text={result.disclaimer} />
      </>
    );
  }

  const pm = result.simple_check?.pm25_lag1;

  return (
    <>
      <h1>Possible patterns</h1>

      <div className="card highlight">
        <p>{result.confidence_note}</p>
      </div>

      {result.factors.map((f) => (
        <div className="card" key={f.factor}>
          <h2 style={{ marginTop: 0 }}>{f.label}</h2>
          <p>
            <span className="badge">{f.verdict}</span>
          </p>
          {f.range_low === null ? (
            <p className="muted">Not enough data to judge this factor yet.</p>
          ) : (
            <p className="muted">
              Odds ratio {f.odds_ratio} per standard deviation
              (range {f.range_low} to {f.range_high}).
            </p>
          )}
        </div>
      ))}

      {pm && pm.attack_rate_above_median !== null && pm.attack_rate_below_median !== null && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Simple check</h2>
          <p>
            After higher-than-median PM2.5 days, attacks happened on{" "}
            {Math.round(pm.attack_rate_above_median * 100)}% of days.
            After lower-than-median days: {Math.round(pm.attack_rate_below_median * 100)}%.
          </p>
        </div>
      )}

      <Disclaimer text={result.disclaimer} />

      <button className="btn btn-block" style={{ marginTop: 16 }} onClick={load}>
        Refresh
      </button>
    </>
  );
}
