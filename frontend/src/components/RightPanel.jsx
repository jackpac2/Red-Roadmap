import { Leaf, PieChart, Play, Settings, TimerReset } from "lucide-react";
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
      <section className="rounded-lg border border-line bg-panel/85 p-5 shadow-panel">
        <div className="mb-4 flex items-center justify-between">
          <div className="text-base font-black uppercase text-text">Focus Timer</div>
          <Settings size={16} className="text-muted" />
        </div>
        <div className="flex gap-2">
          {[25, 50, 90].map((value) => (
            <button
              key={value}
              onClick={() => setMinutes(value)}
              className={`flex-1 rounded-lg border px-2 py-2.5 text-xs font-black transition ${
                minutes === value ? "border-neon bg-neon text-ink shadow-neon" : "border-line bg-ink/70 text-muted hover:border-neon hover:text-text"
              }`}
            >
              {value} min
            </button>
          ))}
        </div>
        <div className="py-7 text-center">
          <Leaf size={30} className="mx-auto mb-3 text-neon" />
          <div className="text-5xl font-black leading-none text-text">{String(minutes).padStart(2, "0")}:00</div>
          <div className="mt-2 text-sm font-semibold text-neonSoft">Ready to focus</div>
        </div>
        <button className="btn-primary inline-flex w-full items-center justify-center gap-2">
          <Play size={16} /> Start
        </button>
      </section>

      <section className="rounded-lg border border-line bg-panel/85 p-5 shadow-panel">
        <div className="mb-4 flex items-center gap-2 text-base font-black uppercase text-text">
          <PieChart size={17} className="text-gold" /> Priority Breakdown
        </div>
        <div className="space-y-3">
          {breakdown.map((item) => (
            <div key={item.priority}>
              <div className="mb-1 flex items-center justify-between text-xs font-bold text-muted">
                <span>{item.priority}</span>
                <span>{item.percent}% ({item.count})</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-line/70">
                <div
                  className={`h-full rounded-full ${item.priority === "HIGH" ? "bg-gold" : item.priority === "MEDIUM" ? "bg-neon" : "bg-moss"}`}
                  style={{ width: `${item.percent}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-line bg-panel/85 p-5 shadow-panel">
        <div className="mb-4 flex items-center gap-2 text-base font-black uppercase text-text">
          <TimerReset size={17} className="text-gold" /> Daily Trail
        </div>
        <div className="text-3xl font-black text-text">{streak}/7</div>
        <div className="mt-1 text-sm font-semibold text-muted">{completed}/{total} missions completed</div>
        <div className="mt-4 grid grid-cols-7 gap-2">
          {Array.from({ length: 7 }).map((_, index) => (
            <div key={index} className={`h-12 rounded-full ${index < streak ? "bg-neon shadow-neon" : "bg-ink/90"}`} />
          ))}
        </div>
      </section>
    </aside>
  );
}
