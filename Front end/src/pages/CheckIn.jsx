import { useEffect, useState } from "react";
import { api } from "../api.js";
import { saveCheckin, localIso } from "../offlineQueue.js";

const today = () => localIso().slice(0, 10);

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return localIso(d).slice(0, 10);
}

export default function CheckIn({ profileId }) {
  const [answer, setAnswer] = useState(null); // true = had symptoms, false = symptom-free, null = not answered
  const [history, setHistory] = useState([]);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadHistory();
  }, [profileId]);

  async function loadHistory() {
    try {
      const rows = await api.listCheckins(profileId, { from: daysAgo(6), to: today() });
      setHistory(rows);
      const todays = rows.find((r) => r.checkin_date === today());
      setAnswer(todays ? todays.had_symptoms : null);
    } catch {
      setNote("Offline. Your history will appear when you are back online.");
    }
  }

  async function choose(hadSymptoms) {
    setSaving(true);
    setNote("");
    try {
      const { queued } = await saveCheckin({
        profile_id: profileId,
        checkin_date: today(),
        had_symptoms: hadSymptoms,
      });
      setAnswer(hadSymptoms);
      setNote(queued
        ? "Saved on this phone. It will upload when you are online."
        : "Check-in saved.");
      if (!queued) loadHistory();
    } catch (err) {
      setNote(`Could not save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <h1>Today's check-in</h1>
      <p>Did you have any asthma symptoms today?</p>
      <p className="muted">
        Only days you answer count as symptom-free. A day with no answer is never assumed to be fine.
      </p>

      <div className="choices" style={{ marginTop: 16 }}>
        <button
          className={`choice ${answer === false ? "selected" : ""}`}
          onClick={() => choose(false)}
          disabled={saving}
        >
          No, symptom-free
        </button>
        <button
          className={`choice ${answer === true ? "selected" : ""}`}
          onClick={() => choose(true)}
          disabled={saving}
        >
          Yes, symptoms
        </button>
      </div>

      {note && <p className="muted" style={{ marginTop: 12 }}>{note}</p>}

      <h2>Last 7 days</h2>
      <ul className="list">
        {Array.from({ length: 7 }, (_, i) => daysAgo(6 - i)).map((day) => {
          const row = history.find((r) => r.checkin_date === day);
          let status = "Not answered";
          if (row) status = row.had_symptoms ? "Symptoms" : "Symptom-free";
          return (
            <li key={day}>
              <strong>{day}</strong> <span className="muted">· {status}</span>
            </li>
          );
        })}
      </ul>
    </>
  );
}
