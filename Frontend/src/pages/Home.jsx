import { useEffect, useState } from "react";
import { api } from "../api.js";
import { logAttack } from "../offlineQueue.js";

const FALLBACK_DISTRICT = "Coimbatore";

function fmt(iso) {
  return iso.replace("T", " ").slice(0, 16);
}

export default function Home({ profileId, navigate }) {
  const [district, setDistrict] = useState(FALLBACK_DISTRICT);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [recent, setRecent] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api.listProfiles()
      .then((profiles) => {
        const me = profiles.find((p) => p.id === profileId);
        if (!cancelled && me?.district) setDistrict(me.district);
      })
      .catch(() => {}); // offline: keep the fallback district
    return () => {
      cancelled = true;
    };
  }, [profileId]);

  useEffect(() => {
    api.listAttacks(profileId)
      .then((rows) => setRecent(rows.slice(0, 5)))
      .catch(() => setRecent([]));
  }, [profileId]);

  async function handleAttack() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const { id, queued } = await logAttack({ profileId, district });
      navigate("followup", { attackId: id, queued });
    } catch (err) {
      setError(`Could not save: ${err.message}`);
      setBusy(false);
    }
  }

  return (
    <>
      <h1>TriggerTrace</h1>

      <div className="warn-box">
        <strong>During a severe attack,</strong> use your inhaler and follow your asthma action plan,
        or call emergency services first. Log the attack afterwards.
      </div>

      <button className="btn-attack" onClick={handleAttack} disabled={busy}>
        {busy ? "Saving..." : "Attack now"}
        <small>Tap once. Details can wait.</small>
      </button>

      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}

      <p className="muted" style={{ marginTop: 12 }}>
        Location used: {district}
      </p>

      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn btn-secondary" onClick={() => navigate("addpast")}>
          Log a past attack
        </button>
        <button className="btn btn-secondary" onClick={() => navigate("checkin")}>
          Today's check-in
        </button>
      </div>

      <h2>Recent attacks</h2>
      {recent === null && <p className="muted">Loading...</p>}
      {recent && recent.length === 0 && (
        <p className="muted">No attacks yet. Tap Attack now when one happens.</p>
      )}
      {recent && recent.length > 0 && (
        <ul className="list">
          {recent.map((a) => (
            <li key={a.id}>
              <strong>{fmt(a.attacked_at)}</strong>
              <div className="muted">
                Severity: {a.severity || "not recorded"} ·
                Inhaler: {a.inhaler_used === null ? "not recorded" : a.inhaler_used ? "yes" : "no"}
              </div>
              {a.logged_later && <span className="badge later">logged later</span>}
            </li>
          ))}
        </ul>
      )}
    </>
  );
      }
