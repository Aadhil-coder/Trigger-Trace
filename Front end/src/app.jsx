import { useEffect, useState } from "react";
import Home from "./pages/Home.jsx";
import FollowUp from "./pages/FollowUp.jsx";
import AddPast from "./pages/AddPast.jsx";
import CheckIn from "./pages/CheckIn.jsx";
import Patterns from "./pages/Patterns.jsx";
import Summary from "./pages/Summary.jsx";
import Settings from "./pages/Settings.jsx";
import SafetyNotice from "./components/SafetyNotice.jsx";
import { getProfileId, setProfileId } from "./api.js";
import { flushQueue, pendingCount, subscribe } from "./offlineQueue.js";

const SAFETY_KEY = "tt_safety_ack";
const RETRY_MS = 30000;

const TABS = [
  { id: "home", label: "Attack" },
  { id: "checkin", label: "Check-in" },
  { id: "patterns", label: "Patterns" },
  { id: "summary", label: "Doctor" },
  { id: "settings", label: "Settings" },
];

export default function App() {
  const [screen, setScreen] = useState({ name: "home", params: {} });
  const [profileId, setProfile] = useState(getProfileId());
  const [acknowledged, setAcknowledged] = useState(localStorage.getItem(SAFETY_KEY) === "yes");
  const [pending, setPending] = useState(pendingCount());

  // Keep the "saved offline" count up to date
  useEffect(() => subscribe(setPending), []);

  // Send queued items on start, when the phone comes back online, and every 30 seconds
  useEffect(() => {
    flushQueue();
    const onOnline = () => flushQueue();
    window.addEventListener("online", onOnline);
    const timer = setInterval(flushQueue, RETRY_MS);
    return () => {
      window.removeEventListener("online", onOnline);
      clearInterval(timer);
    };
  }, []);

  const navigate = (name, params = {}) => setScreen({ name, params });

  const changeProfile = (id) => {
    setProfileId(id);
    setProfile(id);
  };

  if (!acknowledged) {
    return (
      <SafetyNotice
        onAccept={() => {
          localStorage.setItem(SAFETY_KEY, "yes");
          setAcknowledged(true);
        }}
      />
    );
  }

  const shared = { profileId, navigate, params: screen.params };
  let page;
  switch (screen.name) {
    case "followup":
      page = <FollowUp {...shared} />;
      break;
    case "addpast":
      page = <AddPast {...shared} />;
      break;
    case "checkin":
      page = <CheckIn {...shared} />;
      break;
    case "patterns":
      page = <Patterns {...shared} />;
      break;
    case "summary":
      page = <Summary {...shared} />;
      break;
    case "settings":
      page = <Settings {...shared} onProfileChange={changeProfile} />;
      break;
    default:
      page = <Home {...shared} />;
  }

  return (
    <div className="app">
      {pending > 0 && (
        <div className="sync-banner" role="status">
          {pending} saved on this phone. They will upload when you are online.
        </div>
      )}

      <main className="screen">{page}</main>

      <nav className="tabbar" aria-label="Main">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${screen.name === tab.id ? "active" : ""}`}
            onClick={() => navigate(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
