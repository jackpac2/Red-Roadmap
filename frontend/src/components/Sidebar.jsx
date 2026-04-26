import { BarChart3, CalendarClock, CheckCircle2, Gauge, Map, Settings, TreePine } from "lucide-react";
import forestSidebar from "../assets/forest-sidebar.png";
import roadmapEmblem from "../assets/roadmap-emblem.png";

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
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-line bg-ink/92 px-4 py-6 backdrop-blur lg:block">
      <div className="mb-9 flex items-center gap-3 px-1">
        <img src={roadmapEmblem} alt="" className="h-14 w-14 rounded-full border border-neon/50 object-cover shadow-neon" />
        <div>
          <div className="text-lg font-black leading-tight text-text">RED</div>
          <div className="text-sm font-black leading-tight text-neonSoft">ROADMAP</div>
        </div>
      </div>
      <nav className="space-y-2">
        {nav.map(([label, Icon], index) => (
          <button
            key={label}
            className={`flex w-full items-center gap-4 rounded-lg border px-4 py-3 text-left text-sm font-black transition ${
              index === 0
                ? "border-neon/45 bg-neon/20 text-text shadow-neon"
                : "border-transparent text-neonSoft/85 hover:border-line hover:bg-panelSoft/80 hover:text-text"
            }`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
      <div
        className="relative mt-9 min-h-[360px] overflow-hidden rounded-lg border border-line bg-cover bg-center p-5 shadow-panel"
        style={{ backgroundImage: `url(${forestSidebar})` }}
      >
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(8,13,8,0.60),rgba(8,13,8,0.28)_42%,rgba(7,10,7,0.88))]" />
        <div className="relative flex h-full min-h-[320px] flex-col items-center justify-center text-center">
          <TreePine size={42} className="mb-6 text-neon/75" />
          <div className="text-xl font-black leading-tight text-text">
            Focus today,
            <br />
            build tomorrow.
          </div>
          <div className="mt-6 max-w-[150px] text-sm font-semibold leading-relaxed text-neonSoft/90">Consistency is your compass.</div>
        </div>
      </div>
    </aside>
  );
}
