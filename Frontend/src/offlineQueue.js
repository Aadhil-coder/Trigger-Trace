// Saves attacks, follow-ups and check-ins on the phone when there is no internet,
// then uploads them in the same order when the connection returns.

import { api, ApiError } from "./api.js";

const QUEUE_KEY = "tt_queue";
const IDMAP_KEY = "tt_id_map"; // phone-side id -> server id, after upload
const listeners = new Set();
let flushing = false;

function read(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function write(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

export function pendingCount() {
  return read(QUEUE_KEY, []).length;
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notify() {
  const count = pendingCount();
  listeners.forEach((listener) => listener(count));
}

// Local time as "2026-11-18T14:05:00" (the format the backend expects)
export function localIso(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  );
}

export const isLocalId = (id) => typeof id === "string" && id.startsWith("local-");

function newLocalId() {
  return `local-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function enqueue(item) {
  const queue = read(QUEUE_KEY, []);
  queue.push({ ...item, queuedAt: new Date().toISOString() });
  write(QUEUE_KEY, queue);
  notify();
}

// fetch() throws a TypeError when there is no connection
function isNetworkError(err) {
  return err instanceof TypeError || (typeof navigator !== "undefined" && navigator.onLine === false);
}

function resolveId(id) {
  return read(IDMAP_KEY, {})[id] ?? id;
}

// ----- Functions the screens use -----

// One-tap attack. `live: true` tells the backend this happened now, not earlier.
export async function logAttack({ profileId, district, attacked_at, live = true }) {
  const payload = {
    profile_id: profileId,
    district,
    attacked_at: attacked_at ?? localIso(),
    live: attacked_at ? false : live,
  };

  try {
    const saved = await api.createAttack(payload);
    return { id: saved.id, queued: false };
  } catch (err) {
    if (!isNetworkError(err)) throw err;
    const localId = newLocalId();
    enqueue({ type: "attack", localId, payload });
    return { id: localId, queued: true };
  }
}

export async function saveFollowUp(attackId, data) {
  const id = resolveId(attackId);

  if (isLocalId(id)) {
    enqueue({ type: "followup", attackId: id, payload: data });
    return { queued: true };
  }

  try {
    await api.updateAttack(id, data);
    return { queued: false };
  } catch (err) {
    if (!isNetworkError(err)) throw err;
    enqueue({ type: "followup", attackId: id, payload: data });
    return { queued: true };
  }
}

export async function saveCheckin(data) {
  try {
    await api.saveCheckin(data);
    return { queued: false };
  } catch (err) {
    if (!isNetworkError(err)) throw err;
    enqueue({ type: "checkin", payload: data });
    return { queued: true };
  }
}

// ----- Upload -----

// Uploads queued items in order. Stops at the first network error and keeps the rest.
// Items the server rejects stay in the queue with an error note, so no data is lost silently.
export async function flushQueue() {
  if (flushing || (typeof navigator !== "undefined" && navigator.onLine === false)) return 0;
  flushing = true;

  let synced = 0;
  const queue = read(QUEUE_KEY, []);
  const remaining = [];

  try {
    for (let i = 0; i < queue.length; i++) {
      const op = queue[i];
      try {
        if (op.type === "attack") {
          const saved = await api.createAttack(op.payload);
          const map = read(IDMAP_KEY, {});
          map[op.localId] = saved.id;
          write(IDMAP_KEY, map);
        } else if (op.type === "followup") {
          const id = resolveId(op.attackId);
          if (isLocalId(id)) {
            remaining.push(op); // its attack has not uploaded yet
            continue;
          }
          await api.updateAttack(id, op.payload);
        } else if (op.type === "checkin") {
          await api.saveCheckin(op.payload);
        }
        synced += 1;
      } catch (err) {
        if (isNetworkError(err)) {
          remaining.push(...queue.slice(i));
          break;
        }
        const reason = err instanceof ApiError ? err.message : "Unknown error";
        remaining.push({ ...op, error: reason });
      }
    }
  } finally {
    write(QUEUE_KEY, remaining);
    flushing = false;
    notify();
  }
  return synced;
}
