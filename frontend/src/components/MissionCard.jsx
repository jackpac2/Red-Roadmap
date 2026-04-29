import { AlarmClock, CheckCircle2, Pencil, Play, Trash2 } from "lucide-react";
import { StepList } from "./StepList.jsx";

const priorityClass = {
  HIGH: "border-rose-400/70 bg-rose-500/10 text-rose-100",
  MEDIUM: "border-gold/70 bg-gold/10 text-neonSoft",
  LOW: "border-moss/70 bg-moss/15 text-emerald-100"
};

function reminderStatus(reminderAt, status) {
  if (!reminderAt) return "Reminder off";
  const date = new Date(reminderAt);
  if (Number.isNaN(date.getTime())) return "Reminder saved";
  if (status === "COMPLETED") return `Completed mission, reminder saved for ${date.toLocaleString()}`;
  if (date.getTime() <= Date.now()) return `Due now: ${date.toLocaleString()}`;
  return `Armed for ${date.toLocaleString()}`;
}

export function MissionCard({ mission, actions }) {
  const title = mission?.title || "Untitled mission";
  const priority = mission?.priority || "MEDIUM";
  const mode = String(mission?.mode || "FLEXIBLE").replace("_", " ");
  const status = mission?.status || "PENDING";
  const snoozeCount = Number.isFinite(Number(mission?.snooze_count)) ? Number(mission.snooze_count) : 0;
  const completed = status === "COMPLETED";

  return (
    <article className={`rounded-lg border p-4 shadow-panel transition ${
      completed
        ? "border-emerald-400/70 bg-emerald-400/10 shadow-[0_18px_60px_rgba(16,185,129,0.14)] hover:border-emerald-300"
        : "border-line bg-panel/85 hover:border-neon/50"
    }`}>
      <div className="flex flex-col gap-3">
        <h3 className="min-w-0 break-words text-lg font-black leading-snug text-text" title={title}>{title}</h3>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className={`badge ${priorityClass[priority] || ""}`}>{priority}</span>
            <span className="badge border-line bg-panelSoft text-muted">{mode}</span>
            <span className={`badge ${completed ? "border-emerald-400/70 bg-emerald-400/15 text-emerald-100" : "border-neon/50 bg-neon/10 text-neonSoft"}`}>{status}</span>
            <span className={`badge inline-flex items-center gap-1 ${mission?.reminder_at ? "border-neon/50 bg-neon/10 text-neonSoft" : "border-line bg-panelSoft text-muted"}`}>
              <AlarmClock size={13} /> {reminderStatus(mission?.reminder_at, status)}
            </span>
            {snoozeCount > 0 && <span className="badge border-purple-400/50 bg-purple-500/10 text-purple-100">Snoozed {snoozeCount}</span>}
          </div>
          <div className="flex shrink-0 flex-wrap gap-2 lg:justify-end">
            <button onClick={() => actions.start(mission.id)} className="icon-btn" title="Start mission"><Play size={16} /></button>
            <button onClick={() => actions.complete(mission.id, status !== "COMPLETED")} className="icon-btn primary" title="Complete mission"><CheckCircle2 size={16} /></button>
            <button onClick={() => actions.edit(mission)} className="icon-btn" title="Edit mission"><Pencil size={16} /></button>
            <button onClick={() => actions.delete(mission.id)} className="icon-btn danger" title="Delete mission"><Trash2 size={16} /></button>
          </div>
        </div>
      </div>
      <StepList
        mission={mission}
        onAddStep={actions.addStep}
        onCompleteStep={actions.completeStep}
        onUpdateStep={actions.updateStep}
        onDeleteStep={actions.deleteStep}
      />
    </article>
  );
}
