import { useEffect, useState } from "react";
import { api } from "../api.js";
import { logAttack, saveFollowUp, localIso } from "../offlineQueue.js";

export default function AddPast({ profileId, navigate }) {
  const [when, setWhen] = useState(() => localIso().slice(0, 16));
  const [severity, setSeverity] = useState("");
  const [inhaler, setInhaler] = useState(""); // "", "yes" or "no"
  const [district, setDistrict] = useState("Coimbatore");
  const [status, setStatus] = useState("idle"); // idle | saving | saved | error
  const [note, setNote] = useState("");

  useEffect(() => {
    api.listProfiles()
      .then((profiles) => {
        const me = profiles.find((p) => p.id === profileId);
        if (me?.district) setDistrict(me.district);
      })
      .catch(() => {});
  }, [profileId]);

  async function save(event) {
    event.preventDefault();
    const picked = new Date(when);
    if (!when || Number.isNaN(picked.getTime())) {
      setNote("Please pick a date and time.");
      return;
    }
    if (picked > new Date()) {
      setNote("The time cannot be in the future. Use Attack now for an attack that is happening.");
      return;
    }

    setStatus("saving");
    setNote("");
    try {
      // The input gives "2026-11-18T14:05"; the backend expects seconds too
      const attackedAt = when.length === 16 ? `${when}:00` : when;
      const { id, queued } = await logAttack({ profileId, district, attacked_at: attackedAt });

      const followUp = {};
      if (severity) followUp.severity = severity;
      if (inhaler) followUp.inhaler_used = inhaler === "yes";
      if (Object.keys(followUp).length > 0) {
        await saveFollowUp(id, followUp);
      }

      setStatus("saved");
      setNote(queued
        ? "Saved on this phone. It will upload when you are online."
        : "Past attack saved and marked as logged later.");
    } catch (err) {
      setStatus("error");
      setNote(`Could not save: ${err.message}`);
    }
  }

  if (status === "saved") {
    return (
      <div className="card highlight">
        <h1>Saved</h1>
        <p className="ok-text">{note}</p>
        <button className="btn btn-primary btn-block" onClick={() => navigate("home")}>Done</button>
      </div>
    );
  }

  return (
    <>
      <h1>Log a past attack</h1>
      <p className="muted">Use this for an attack that already happened. It is marked "logged later".</p>

      <form className="stack" onSubmit={save}>
        <div className="field">
          <label htmlFor="when">When did it happen?</label>
          <input
            id="when"
            type="datetime-local"
            value={when}
            onChange={(e) => setWhen(e.target.value)}
            required
          />
        </div>

        <div className="field">
          <span className="label">Severity (optional)</span>
          <div className="choices choices-3">
            {["mild", "moderate", "severe"].map((s) => (
              <button
                type="button"
                key={s}
                className={`choice ${severity === s ? "selected" : ""}`}
                onClick={() => setSeverity(severity === s ? "" : s)}
              >
                {s[0].toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <span className="label">Inhaler used? (optional)</span>
          <div className="choices">
            {["yes", "no"].map((v) => (
              <button
                type="button"
                key={v}
                className={`choice ${inhaler === v ? "selected" : ""}`}
                onClick={() => setInhaler(inhaler === v ? "" : v)}
              >
                {v[0].toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {note && <p className="error-text">{note}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={status === "saving"}>
          {status === "saving" ? "Saving..." : "Save past attack"}
        </button>
        <button type="button" className="btn btn-block" onClick={() => navigate("home")}>
          Cancel
        </button>
      </form>
    </>
  );
}
