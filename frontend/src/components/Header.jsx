import { CalendarDays, Clock3, Plus, Trash2 } from "lucide-react";
import forestHero from "../assets/forest-hero.png";

export function Header({ now, score, onCreate, onDeleteAll, hasMissions }) {
  const current = new Date(now);
  const dateLabel = Number.isNaN(current.getTime())
    ? new Date().toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
    : current.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  const timeLabel = Number.isNaN(current.getTime())
    ? now
    : current.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });

  return (
    <header
      className="relative overflow-hidden rounded-lg border border-line bg-cover bg-center p-6 shadow-panel md:p-8"
      style={{ backgroundImage: `url(${forestHero})` }}
    >
      <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(10,16,10,0.80),rgba(17,26,18,0.42)_42%,rgba(7,11,7,0.82))]" />
      <div className="absolute inset-0 border border-neon/10" />
      <div className="relative flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0">
          <h1 className="text-3xl font-black leading-tight text-text md:text-4xl">Good evening, Gino.</h1>
          <p className="mt-2 text-base font-semibold text-neonSoft/90">Mission control for daily execution.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-[148px] rounded-lg border border-line/80 bg-panel/80 px-4 py-3 shadow-panel backdrop-blur">
            <div className="flex items-center gap-2 text-xs font-black uppercase text-muted">
              <CalendarDays size={15} /> Date / Time
            </div>
            <div className="mt-2 text-sm font-bold text-muted">{dateLabel}</div>
            <div className="mt-1 flex items-center gap-2 text-2xl font-black text-text">
              <Clock3 size={16} className="text-neon" /> {timeLabel}
            </div>
          </div>
          <div className="min-w-[148px] rounded-lg border border-line/80 bg-panel/80 px-4 py-3 shadow-panel backdrop-blur">
            <div className="text-xs font-black uppercase text-gold">Execution Score</div>
            <div className="mt-3 text-3xl font-black text-text">{score}%</div>
          </div>
          <button onClick={onDeleteAll} disabled={!hasMissions} className="inline-flex min-h-[58px] items-center gap-2 rounded-lg border border-line bg-panel/75 px-5 py-3 text-sm font-black text-muted shadow-panel transition hover:border-rose-300/70 hover:bg-rose-500/10 hover:text-rose-100 disabled:cursor-not-allowed disabled:opacity-45">
            <Trash2 size={18} /> Delete All
          </button>
          <button onClick={onCreate} className="inline-flex min-h-[58px] items-center gap-2 rounded-lg border border-neon bg-neon px-5 py-3 text-sm font-black text-ink shadow-neon transition hover:bg-neonSoft">
            <Plus size={18} /> New Mission
          </button>
        </div>
      </div>
    </header>
  );
}
