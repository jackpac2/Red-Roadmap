import { CircleDot } from "lucide-react";
import forestTrail from "../assets/forest-trail.png";

export function MissionTimeline({ items }) {
  const timelineItems = Array.isArray(items) ? items : [];

  return (
    <section className="overflow-hidden rounded-lg border border-line bg-panel/85 shadow-panel">
      <div
        className="relative min-h-[300px] bg-cover bg-center p-5 2xl:min-h-[440px]"
        style={{ backgroundImage: `url(${forestTrail})` }}
      >
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(8,13,8,0.62),rgba(8,13,8,0.18)_48%,rgba(8,13,8,0.86))]" />
        <div className="relative text-base font-black uppercase text-text">Mission Timeline</div>
      </div>
      <div className="max-h-[300px] space-y-3 overflow-auto p-4">
        {timelineItems.slice(0, 14).map((item) => {
          const status = item?.status || "PENDING";

          return (
            <div key={item?.id || item?.title} className="flex gap-3 rounded-lg border border-transparent p-2 transition hover:border-neon/50 hover:bg-panelSoft">
              <CircleDot size={16} className={status === "COMPLETED" ? "mt-1 text-emerald-300" : "mt-1 text-gold"} />
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-text">{item?.title || "Untitled mission"}</div>
                <div className="text-xs font-semibold text-muted">{status} &middot; {item?.priority || "MEDIUM"}</div>
              </div>
            </div>
          );
        })}
        {!timelineItems.length && <div className="text-sm font-semibold text-muted">No timeline items yet.</div>}
      </div>
    </section>
  );
}
