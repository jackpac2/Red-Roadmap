import { CheckCircle2, Hourglass, Leaf, PauseCircle, TreePine } from "lucide-react";

const cards = [
  ["Active", "active_tasks", Leaf],
  ["Pending", "pending_tasks", Hourglass],
  ["Completed", "completed_tasks", CheckCircle2],
  ["Away", "away_tasks", TreePine],
  ["Snoozed", "snoozed_tasks", PauseCircle]
];

export function StatsCards({ stats }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map(([label, key, Icon]) => (
        <div key={key} className="rounded-lg border border-line bg-panel/80 p-5 shadow-panel transition hover:border-neon/50">
          <div className="flex items-center gap-5">
            <Icon size={25} className="shrink-0 text-gold" />
            <div>
              <div className="text-xs font-black uppercase text-neonSoft">{label}</div>
              <div className="mt-2 text-3xl font-black leading-none text-text">{stats?.[key] ?? 0}</div>
            </div>
          </div>
        </div>
      ))}
    </section>
  );
}
