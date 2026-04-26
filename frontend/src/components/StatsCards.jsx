import { Activity, CheckCircle2, Moon, PauseCircle, TimerReset } from "lucide-react";

const cards = [
  ["Active", "active_tasks", Activity],
  ["Pending", "pending_tasks", TimerReset],
  ["Completed", "completed_tasks", CheckCircle2],
  ["Away", "away_tasks", Moon],
  ["Snoozed", "snoozed_tasks", PauseCircle]
];

export function StatsCards({ stats }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map(([label, key, Icon]) => (
        <div key={key} className="rounded-lg border border-line bg-gradient-to-br from-panel to-panelSoft/65 p-4 shadow-panel transition hover:border-neon/50">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-black uppercase">{label}</span>
            <Icon size={18} className="text-neon" />
          </div>
          <div className="mt-3 text-3xl font-black text-text">{stats?.[key] ?? 0}</div>
        </div>
      ))}
    </section>
  );
}
