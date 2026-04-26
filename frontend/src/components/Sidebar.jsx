import { BarChart3, CalendarClock, CheckCircle2, Gauge, Map, Settings, TimerReset } from "lucide-react";

const nav = [
  ["Dashboard", Gauge],
  ["Roadmap", Map],
  ["Timeline", CalendarClock],
  ["Completed", CheckCircle2],
  ["Analytics", BarChart3],
  ["Settings", Settings]
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-line/70 bg-black/25 px-4 py-5 backdrop-blur lg:block">
      <div className="mb-8 flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-lg border border-neon/70 bg-gradient-to-br from-neon/25 to-cyanLine/15 text-xl font-black text-neon shadow-neon">R</div>
        <div>
          <div className="text-sm font-black text-text">RED</div>
          <div className="text-xs font-semibold text-muted">ROADMAP</div>
        </div>
      </div>
      <nav className="space-y-2">
        {nav.map(([label, Icon], index) => (
          <button
            key={label}
            className={`flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left text-sm font-semibold transition ${
              index === 0
                ? "border-neon/60 bg-neon/10 text-text shadow-neon"
                : "border-transparent text-muted hover:border-cyanLine/50 hover:bg-panelSoft hover:text-text"
            }`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
      <div className="mt-8 rounded-lg border border-neon/30 bg-neon/10 p-4">
        <TimerReset size={24} className="mb-3 text-neon" />
        <div className="text-sm font-black text-text">Stay focused.</div>
        <div className="mt-1 text-xs font-semibold text-muted">Execute daily. Win consistently.</div>
      </div>
    </aside>
  );
}
