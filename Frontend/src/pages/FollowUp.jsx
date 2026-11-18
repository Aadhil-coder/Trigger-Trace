import { useState } from "react";
import { saveFollowUp } from "../offlineQueue.js";

const SEVERITIES = [
  { value: "mild", label: "Mild" },
  { value: "moderate", label: "Moderate" },
  { value: "severe", label: "Severe" },
];

export default function FollowUp({ navigate, params }) {
  const attackId = params.attackId;
  const [severity, setSeverity] = useState(null);
  const [inhaler, setInhaler] = useState(null); // true, false or null
  const [status, setStatus] = useState("idle"); // idle | saving | saved | error
  const [note, setNote] = useState("");

  if (!attackId) {
    return (
      <div className="card">
        <p>No attack selected.</p>
        <button className="btn btn-block" onClick={() => navigate("home")}>Back to home</button>
      </div>
    );
  }

  async function save() {
    if (!severity || inhaler === null) {
      setNote("Please choose a severity and whether you used your inhaler.");
      return;
    }
    setStatus("saving");
    setNote("");
    try {
      const { queued } = await saveFollowUp(attackId, { severity, inhaler_used: inhaler });
      setStatus("saved");
      setNote(queued
        ? "Saved on this phone. It will upload when you are online."
        : "Saved. Thank you.");
    } catch (err) {
      setStatus("error");
      setNote(`Could not save: ${err.message}`);
    }
  }

  if (status === "saved") {
    return (
      <div className="card highlight">
        <h1>Recorded</h1>
        <p className="ok-text">{note}</p>
        <button className="btn btn-primary btn-block" onClick={() => navigate("home")}>Done</button>
      </div>
    );
  }

  return (
    <>
      <h1>How was the attack?</h1>
      <p className="muted">Answer when you feel calm. This can wait.</p>

      <div className="field" style={{ marginBottom: 20 }}>
        <span className="label">Severity</span>
        <div className="choices choices-3">
          {SEVERITIES.map((s) => (
            <button
              key={s.value}
              className={`choice ${severity === s.value ? "selected" : ""}`}
              onClick={() => setSeverity(s.value)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field" style={{ marginBottom: 20 }}>
        <span className="label">Did you use your inhaler?</span>
        <div className="choices">
          <button
            className={`choice ${inhaler === true ? "selected" : ""}`}
            onClick={() => setInhaler(true)}
          >
            Yes
          </button>
          <button
            className={`choice ${inhaler === false ? "selected" : ""}`}
            onClick={() => setInhaler(false)}
          >
            No
          </button>
        </div>
      </div>

      {note && <p className="error-text">{note}</p>}

      <div className="stack">
        <button
          className="btn btn-primary btn-block"
          onClick={save}
          disabled={status === "saving"}
        >
          {status === "saving" ? "Saving..." : "Save"}
        </button>
        <button className="btn btn-block" onClick={() => navigate("home")}>
          Skip for now
        </button>
      </div>
    </>
  );
}
