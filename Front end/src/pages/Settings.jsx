import { useEffect, useState } from "react";
import { api } from "../api.js";
import { flushQueue, pendingCount } from "../offlineQueue.js";

const SAFETY_KEY = "tt_safety_ack";

export default function Settings({ profileId, onProfileChange }) {
  const [profiles, setProfiles] = useState([]);
  const [offline, setOffline] = useState(false);
  const [district, setDistrict] = useState("");
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState("caregiver");
  const [newDistrict, setNewDistrict] = useState("");
  const [queued, setQueued] = useState(pendingCount());
  const [note, setNote] = useState("");

  useEffect(() => {
    load();
  }, [profileId]);

  async function load() {
    try {
      const rows = await api.listProfiles();
      setProfiles(rows);
      setOffline(false);
      const me = rows.find((p) => p.id === profileId);
      setDistrict(me?.district || "");
    } catch {
      setOffline(true);
    }
  }

  function switchTo(id) {
    onProfileChange(id);
    setNote(`Now using profile ${id}.`);
  }

  async function addProfile() {
    if (!newName.trim()) {
      setNote("Enter a name for the new profile.");
      return;
    }
    try {
      await api.createProfile({ name: newName.trim(), role: newRole, district: newDistrict.trim() || null });
      setNewName("");
      setNewDistrict("");
      setNote("Profile added.");
      load();
    } catch (err) {
      setNote(`Could not add profile: ${err.message}`);
    }
  }

  async function saveDistrict() {
    try {
      await api.updateProfile(profileId, { district: district.trim() || null });
      setNote("District saved.");
      load();
    } catch (err) {
      setNote(`Could not save district: ${err.message}`);
    }
  }

  async function uploadNow() {
    const sent = await flushQueue();
    setQueued(pendingCount());
    setNote(pendingCount() === 0
      ? `Uploaded ${sent} saved item(s).`
      : "Some items could not upload yet. They will try again.");
  }

  async function deleteMyData() {
    if (!window.confirm("Delete all attacks and check-ins for this profile? This cannot be undone.")) return;
    try {
      await api.deleteProfileData(profileId);
      localStorage.removeItem("tt_queue");
      localStorage.removeItem("tt_id_map");
      setQueued(pendingCount());
      setNote("Your attacks and check-ins were deleted.");
    } catch (err) {
      setNote(`Could not delete: ${err.message}`);
    }
  }

  async function deleteProfile() {
    if (!window.confirm("Delete this profile and everything in it? This cannot be undone.")) return;
    try {
      await api.deleteProfile(profileId);
      localStorage.removeItem("tt_queue");
      localStorage.removeItem("tt_id_map");
      onProfileChange(1);
      setNote("Profile deleted. Switched to profile 1.");
      load();
    } catch (err) {
      setNote(`Could not delete profile: ${err.message}`);
    }
  }

  function showSafetyAgain() {
    localStorage.removeItem(SAFETY_KEY);
    window.location.reload();
  }

  return (
    <>
      <h1>Settings</h1>
      {note && <p className="ok-text">{note}</p>}
      {offline && <p className="warn-box">You are offline. Profiles and district changes need a connection.</p>}

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Profile</h2>
        <p className="muted">Currently logging for profile {profileId}.</p>
        {profiles.length > 0 && (
          <div className="stack">
            {profiles.map((p) => (
              <button
                key={p.id}
                className={`choice ${p.id === profileId ? "selected" : ""}`}
                onClick={() => switchTo(p.id)}
              >
                {p.name} ({p.role}){p.district ? ` · ${p.district}` : ""}
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>District for this profile</h2>
        <p className="muted">Only the district is stored, never an exact address.</p>
        <div className="field">
          <label htmlFor="district">District</label>
          <input
            id="district"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            placeholder="e.g. Coimbatore"
          />
        </div>
        <button className="btn btn-primary btn-block" style={{ marginTop: 12 }} onClick={saveDistrict}>
          Save district
        </button>
      </section>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Add a profile</h2>
        <p className="muted">Use "caregiver" when logging for a child or older adult.</p>
        <div className="stack">
          <div className="field">
            <label htmlFor="newName">Name</label>
            <input id="newName" value={newName} onChange={(e) => setNewName(e.target.value)} />
          </div>
          <div className="choices">
            {["self", "caregiver"].map((r) => (
              <button
                key={r}
                className={`choice ${newRole === r ? "selected" : ""}`}
                onClick={() => setNewRole(r)}
              >
                {r[0].toUpperCase() + r.slice(1)}
              </button>
            ))}
          </div>
          <div className="field">
            <label htmlFor="newDistrict">District (optional)</label>
            <input id="newDistrict" value={newDistrict} onChange={(e) => setNewDistrict(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" onClick={addProfile}>Add profile</button>
        </div>
      </section>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Saved on this phone</h2>
        <p>{queued} item(s) waiting to upload.</p>
        <button className="btn btn-block" onClick={uploadNow}>Upload now</button>
      </section>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Your data</h2>
        <div className="stack">
          <button className="btn btn-danger btn-block" onClick={deleteMyData}>
            Delete this profile's attacks and check-ins
          </button>
          <button className="btn btn-danger btn-block" onClick={deleteProfile}>
            Delete this profile
          </button>
        </div>
      </section>

      <section className="card">
        <h2 style={{ marginTop: 0 }}>Safety notice</h2>
        <button className="btn btn-block" onClick={showSafetyAgain}>Show safety notice again</button>
      </section>
    </>
  );
          }
