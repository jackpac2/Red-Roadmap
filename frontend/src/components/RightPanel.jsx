import { Flame, Pause, PieChart, Play, Settings, TimerReset, Trophy } from "lucide-react";
import { useMemo, useState } from "react";

const priorities = ["HIGH", "MEDIUM", "LOW"];

export function RightPanel({ missions, progress }) {
  const [minutes, setMinutes] = useState(25);
  const missionList = Array.isArray(missions) ? missions : [];
  const breakdown = useMemo(() => {
    const total = Math.max(missionList.length, 1);
    return priorities.map((priority) => {
      const count = missionList.filter((mission) => mission.priority === priority).length;
      return { priority, count, percent: Math.round((count / total) * 100) };
    });
  }, [missionList]);
  const completed = Number(progress?.completed || 0);
  const total = Number(progress?.total || 0);
  const streak = Math.max(0, Math.min(7, completed));

  return (
    <aside className="space-y-4">
      <section className="rounded-lg border border-line bg-panel/95 p-4 shadow-panel">
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm font-black uppercase text-text">Focus Timer</div>
          <Settings size={16} className="text-muted" />
        </div>
        <div className="flex gap-2">
          {[25, 50, 90].map((value) => (
            <button
              key={value}
              onClick={() => setMinutes(value)}
              className={`flex-1 rounded-lg border px-2 py-2 text-xs font-black transition ${
                minutes === value ? "border-neon bg-neon/15 text-neonSoft" : "border-line bg-ink/70 text-muted hover:border-cyanLine"
              }`}
            >
              {value} min
            </button>
          ))}
        </div>
        <div className="py-6 text-center">
          <TimerReset size={28} className="mx-auto mb-2 text-neon" />
          <div className="text-4xl font-black text-neonSoft">{String(minutes).padStart(2, "0")}:00</div>
          <div className="mt-1 text-xs font-semibold text-muted">Ready to focus</div>
        </div>
        <button className="btn-primary inline-flex w-full items-center justify-center gap-2">
          <Play size={16} /> Start
        </button>
      </section>

      <section className="rounded-lg border border-line bg-panel/95 p-4 shadow-panel">
        <div className="mb-4 flex items-center gap-2 text-sm font-black uppercase text-text">
          <PieChart size={16} className="text-neon" /> Priority Breakdown
        </div>
        <div className="space-y-3">
          {breakdown.map((item) => (
            <div key={item.priority}>
              <div className="mb-1 flex items-center justify-between text-xs font-bold text-muted">
                <span>{item.priority}</span>
                <span>{item.percent}% ({item.count})</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-ink">
                <div
                  className={`h-full rounded-full ${item.priority === "HIGH" ? "bg-neon" : item.priority === "MEDIUM" ? "bg-cyanLine" : "bg-emerald-400"}`}
                  style={{ width: `${item.percent}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-line bg-panel/95 p-4 shadow-panel">
        <div className="mb-4 flex items-center gap-2 text-sm font-black uppercase text-text">
          <Trophy size={16} className="text-neon" /> Streak
        </div>
        <div className="flex items-end gap-4">
          <div>
            <div className="flex items-center gap-2 text-3xl font-black text-text">
              <Flame size={26} className="text-neon" /> {streak}
            </div>
            <div className="text-xs font-semibold text-muted">days tracked</div>
          </div>
          <div className="flex flex-1 items-end gap-2 border-l border-line pl-4">
            {Array.from({ length: 7 }).map((_, index) => (
              <div
                key={index}
                className={`h-14 flex-1 rounded-full ${index < streak ? "bg-neon shadow-neon" : "bg-ink"}`}
                style={{ opacity: index < streak ? 0.62 + index * 0.05 : 1 }}
              />
            ))}
          </div>
        </div>
        <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-muted">
          <Pause size={14} /> {completed}/{total} missions completed
        </div>
      </section>
    </aside>
  );
}
