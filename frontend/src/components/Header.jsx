import { CalendarDays, Clock3, Plus } from "lucide-react";

export function Header({ now, score, onCreate }) {
  return (
    <header className="rounded-lg border border-line bg-panel p-5 shadow-panel">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-wide text-neon md:text-4xl">RED ROADMAP</h1>
          <p className="mt-1 text-sm font-medium text-muted">Mission control for daily execution</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-lg border border-cyanLine/60 bg-panelSoft px-4 py-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase text-muted">
              <CalendarDays size={15} /> Date / Time
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm font-semibold text-text">
              <Clock3 size={15} /> {now}
            </div>
          </div>
          <div className="rounded-lg border border-neon/60 bg-neon/10 px-4 py-3">
            <div className="text-xs font-bold uppercase text-neonSoft">Execution Score</div>
            <div className="mt-1 text-2xl font-black text-text">{score}%</div>
          </div>
          <button onClick={onCreate} className="inline-flex items-center gap-2 rounded-lg border border-neon bg-neon px-4 py-3 text-sm font-black text-ink shadow-neon transition hover:bg-neonSoft">
            <Plus size={18} /> Mission
          </button>
        </div>
      </div>
    </header>
  );
}
