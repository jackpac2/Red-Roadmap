import { CircleDot } from "lucide-react";

export function MissionTimeline({ items }) {
  const timelineItems = Array.isArray(items) ? items : [];

  return (
    <section className="rounded-lg border border-line bg-panel/90 p-4 shadow-panel">
      <div className="mb-4 text-sm font-black uppercase text-text">Mission Timeline</div>
      <div className="space-y-3">
        {timelineItems.slice(0, 14).map((item) => {
          const status = item?.status || "PENDING";

          return (
            <div key={item?.id || item?.title} className="flex gap-3 rounded-lg border border-transparent p-2 transition hover:border-cyanLine/50 hover:bg-panelSoft">
              <CircleDot size={16} className={status === "COMPLETED" ? "mt-1 text-emerald-300" : "mt-1 text-neon"} />
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-text">{item?.title || "Untitled mission"}</div>
                <div className="text-xs font-semibold text-muted">{status} &middot; {item?.priority || "MEDIUM"}</div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
