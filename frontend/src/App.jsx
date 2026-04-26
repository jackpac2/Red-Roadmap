import { useEffect, useMemo, useState } from "react";
import { AlarmClock, Bell, BellOff, Clock3 } from "lucide-react";
import { FilterBar } from "./components/FilterBar.jsx";
import { Header } from "./components/Header.jsx";
import { MissionCard } from "./components/MissionCard.jsx";
import { MissionTimeline } from "./components/MissionTimeline.jsx";
import { ProgressBar } from "./components/ProgressBar.jsx";
import { RightPanel } from "./components/RightPanel.jsx";
import { Sidebar } from "./components/Sidebar.jsx";
import { StatsCards } from "./components/StatsCards.jsx";
import { api } from "./lib/api.js";

const EMPTY_STATS = {
  active_tasks: 0,
  pending_tasks: 0,
  completed_tasks: 0,
  away_tasks: 0,
  snoozed_tasks: 0
};

const EMPTY_PROGRESS = {
  total: 0,
  completed: 0,
  percent: 0
};

function localDateTimeForInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function localInputToApi(value) {
  if (!value) return null;
  return value.length === 16 ? `${value}:00` : value;
}

function minutesFromNowForInput(minutes) {
  const date = new Date(Date.now() + minutes * 60 * 1000);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function asObject(value, fallback) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : fallback;
}

function errorMessage(error) {
  return error instanceof Error ? error.message : "Unable to load dashboard data.";
}

export function App() {
  const [missions, setMissions] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [progress, setProgress] = useState(EMPTY_PROGRESS);
  const [score, setScore] = useState(0);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");
  const [priority, setPriority] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [now, setNow] = useState(new Date().toLocaleString());
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const load = async () => {
    setError("");
    const results = await Promise.allSettled([
      api.getMissions(),
      api.getStats(),
      api.getProgress(),
      api.getExecutionScore(),
      api.getTimeline()
    ]);

    const [nextMissions, nextStats, nextProgress, nextScore, nextTimeline] = results;
    setMissions(nextMissions.status === "fulfilled" ? asArray(nextMissions.value) : []);
    setStats(nextStats.status === "fulfilled" ? asObject(nextStats.value, EMPTY_STATS) : EMPTY_STATS);
    setProgress(nextProgress.status === "fulfilled" ? asObject(nextProgress.value, EMPTY_PROGRESS) : EMPTY_PROGRESS);
    setScore(
      nextScore.status === "fulfilled" && Number.isFinite(Number(nextScore.value?.score))
        ? Number(nextScore.value.score)
        : 0
    );
    setTimeline(nextTimeline.status === "fulfilled" ? asArray(nextTimeline.value) : []);

    const failed = results.find((result) => result.status === "rejected");
    if (failed?.status === "rejected") {
      setError(errorMessage(failed.reason));
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
    const clock = setInterval(() => setNow(new Date().toLocaleString()), 1000);
    return () => clearInterval(clock);
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return asArray(missions).filter((mission) => {
      const title = String(mission?.title || "");
      const matchesQuery = !needle || title.toLowerCase().includes(needle);
      const matchesStatus = status === "ALL" || mission.status === status;
      const matchesPriority = priority === "ALL" || mission.priority === priority;
      return matchesQuery && matchesStatus && matchesPriority;
    });
  }, [missions, priority, query, status]);

  const mutate = async (fn) => {
    setError("");
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };

  const openEdit = (mission) => {
    setEditing(mission);
    setFormOpen(true);
  };

  const deleteAll = () => {
    if (!missions.length) return;
    if (confirm("Delete all missions and their steps?")) {
      mutate(() => api.deleteAllMissions());
    }
  };

  const actions = {
    start: (id) => mutate(() => api.startMission(id)),
    complete: (id, completed) => mutate(() => api.completeMission(id, completed)),
    edit: openEdit,
    delete: (id) => {
      if (confirm("Delete this mission and its steps?")) mutate(() => api.deleteMission(id));
    },
    addStep: (id, title) => mutate(() => api.addStep(id, title)),
    completeStep: (id, completed) => mutate(() => api.completeStep(id, completed)),
    updateStep: (step) => {
      const title = prompt("Step title", step.title);
      if (title?.trim()) mutate(() => api.updateStep(step.id, title.trim()));
    },
    deleteStep: (id) => {
      if (confirm("Delete this step?")) mutate(() => api.deleteStep(id));
    },
    updateReminder: (id, reminderAt) => mutate(() => api.updateReminder(id, reminderAt)),
    clearReminder: (id) => mutate(() => api.clearReminder(id)),
    snooze: (id, minutes) => mutate(() => api.snoozeMission(id, minutes))
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(135deg,#030511_0%,#070b1a_46%,#10142a_100%)] text-text">
      <div className="flex">
        <Sidebar />
        <main className="min-w-0 flex-1 p-4 lg:p-6">
          <div className="mx-auto max-w-[1500px] space-y-4">
            <Header now={now} score={score} onCreate={openCreate} onDeleteAll={deleteAll} hasMissions={missions.length > 0} />
            {error && <div className="rounded-lg border border-rose-400/60 bg-rose-500/10 px-4 py-3 text-sm font-semibold text-rose-100">{error}</div>}
            <StatsCards stats={stats} />
            <ProgressBar progress={progress} />
            <div className="grid gap-4 2xl:grid-cols-[300px_minmax(0,1fr)_280px]">
              <MissionTimeline items={timeline} />
              <section className="space-y-3">
                <FilterBar query={query} setQuery={setQuery} status={status} setStatus={setStatus} priority={priority} setPriority={setPriority} />
                {loading ? (
                  <div className="rounded-lg border border-line bg-panel p-8 text-center font-semibold text-muted">Loading missions...</div>
                ) : (
                  <div className="space-y-3">
                    {filtered.map((mission) => <MissionCard key={mission.id} mission={mission} actions={actions} />)}
                    {!filtered.length && <div className="rounded-lg border border-line bg-panel p-8 text-center font-semibold text-muted">No missions found.</div>}
                  </div>
                )}
              </section>
              <RightPanel missions={missions} progress={progress} />
            </div>
          </div>
        </main>
      </div>
      {formOpen && (
        <MissionForm
          mission={editing}
          onClose={() => setFormOpen(false)}
          onSave={(payload) => mutate(async () => {
            if (editing) {
              await api.updateMission(editing.id, payload);
            } else {
              await api.createMission(payload);
            }
            setFormOpen(false);
          })}
        />
      )}
    </div>
  );
}

function MissionForm({ mission, onClose, onSave }) {
  const [title, setTitle] = useState(mission?.title || "");
  const [priority, setPriority] = useState(mission?.priority || "MEDIUM");
  const [mode, setMode] = useState(mission?.mode || "FLEXIBLE");
  const [reminder, setReminder] = useState(localDateTimeForInput(mission?.reminder_at));
  const [reminderEnabled, setReminderEnabled] = useState(Boolean(mission?.reminder_at));
  const reminderDate = reminder ? new Date(reminder) : null;
  const reminderValid = reminderDate && !Number.isNaN(reminderDate.getTime());

  const submit = (event) => {
    event.preventDefault();
    if (!title.trim()) return;
    const payload = {
      title: title.trim(),
      priority,
      mode,
      reminder_at: reminderEnabled && reminder ? localInputToApi(reminder) : null
    };
    onSave(payload);
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4">
      <form onSubmit={submit} className="w-full max-w-lg rounded-lg border border-neon/50 bg-panel p-5 shadow-neon">
        <div className="mb-4 text-lg font-black text-text">{mission ? "Edit Mission" : "Create Mission"}</div>
        <div className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-xs font-black uppercase text-muted">Mission name</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Enter mission name" className="field" autoFocus required />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <select value={priority} onChange={(event) => setPriority(event.target.value)} className="control">
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
            <select value={mode} onChange={(event) => setMode(event.target.value)} className="control">
              <option value="AT_PC">At PC</option>
              <option value="AWAY">Away</option>
              <option value="FLEXIBLE">Flexible</option>
            </select>
          </div>
          <section className="rounded-lg border border-line bg-ink/70 p-4">
            <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <div className="grid h-9 w-9 place-items-center rounded-lg border border-neon/50 bg-neon/10 text-neon">
                  <AlarmClock size={18} />
                </div>
                <div>
                  <div className="text-sm font-black text-text">Reminder schedule</div>
                  <div className="text-xs font-semibold text-muted">
                    {reminderEnabled && reminderValid ? `Alarm armed for ${reminderDate.toLocaleString()}` : "Reminder is off"}
                  </div>
                </div>
              </div>
              <label className="inline-flex items-center gap-2 rounded-lg border border-line bg-panelSoft px-3 py-2 text-xs font-black uppercase text-muted">
                <input
                  type="checkbox"
                  checked={reminderEnabled}
                  onChange={(event) => {
                    setReminderEnabled(event.target.checked);
                    if (event.target.checked && !reminder) {
                      setReminder(minutesFromNowForInput(1));
                    }
                  }}
                  className="accent-neon"
                />
                {reminderEnabled ? <Bell size={15} className="text-neon" /> : <BellOff size={15} />}
                Enabled
              </label>
            </div>
            <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
              <label className="block">
                <span className="mb-1 block text-xs font-black uppercase text-muted">Alarm time</span>
                <input
                  type="datetime-local"
                  value={reminder}
                  disabled={!reminderEnabled}
                  onChange={(event) => setReminder(event.target.value)}
                  className="field disabled:cursor-not-allowed disabled:opacity-45"
                />
              </label>
              <div className="flex items-end gap-2">
                {[1, 5, 15].map((minutes) => (
                  <button
                    key={minutes}
                    type="button"
                    onClick={() => {
                      setReminderEnabled(true);
                      setReminder(minutesFromNowForInput(minutes));
                    }}
                    className="btn-secondary inline-flex items-center gap-2 px-3"
                  >
                    <Clock3 size={14} /> +{minutes}m
                  </button>
                ))}
              </div>
            </div>
          </section>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button disabled={!title.trim() || (reminderEnabled && !reminder)} className="btn-primary disabled:cursor-not-allowed disabled:opacity-45">Save</button>
        </div>
      </form>
    </div>
  );
}
