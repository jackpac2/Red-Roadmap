import { CheckCircle2, Pencil, Play, Trash2 } from "lucide-react";
import { StepList } from "./StepList.jsx";

const priorityClass = {
  HIGH: "border-rose-400/70 bg-rose-500/10 text-rose-100",
  MEDIUM: "border-cyanLine/70 bg-cyanLine/10 text-blue-100",
  LOW: "border-emerald-400/60 bg-emerald-400/10 text-emerald-100"
};

export function MissionCard({ mission, actions }) {
  const title = mission?.title || "Untitled mission";
  const priority = mission?.priority || "MEDIUM";
  const mode = String(mission?.mode || "FLEXIBLE").replace("_", " ");
  const status = mission?.status || "PENDING";
  const snoozeCount = Number.isFinite(Number(mission?.snooze_count)) ? Number(mission.snooze_count) : 0;

  return (
    <article className="rounded-lg border border-line bg-panel p-4 shadow-panel transition hover:border-neon/50">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="min-w-0 flex-1 truncate text-lg font-black text-text">{title}</h3>
            <span className={`badge ${priorityClass[priority] || ""}`}>{priority}</span>
            <span className="badge border-line bg-panelSoft text-muted">{mode}</span>
            <span className="badge border-neon/50 bg-neon/10 text-neonSoft">{status}</span>
          </div>
          <div className="mt-2 text-xs font-semibold text-muted">
            Reminder: {mission?.reminder_at ? new Date(mission.reminder_at).toLocaleString() : "None"} &middot; Snoozed {snoozeCount}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => actions.start(mission.id)} className="icon-btn" title="Start mission"><Play size={16} /></button>
          <button onClick={() => actions.complete(mission.id, status !== "COMPLETED")} className="icon-btn primary" title="Complete mission"><CheckCircle2 size={16} /></button>
          <button onClick={() => actions.edit(mission)} className="icon-btn" title="Edit mission"><Pencil size={16} /></button>
          <button onClick={() => actions.delete(mission.id)} className="icon-btn danger" title="Delete mission"><Trash2 size={16} /></button>
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
