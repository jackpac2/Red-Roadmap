export function ProgressBar({ progress }) {
  const percent = progress?.percent ?? 0;
  return (
    <section className="rounded-lg border border-line bg-panel/80 p-5 shadow-panel">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <div className="text-base font-black uppercase text-text">Overall Progress</div>
          <div className="mt-1 text-sm font-semibold text-neonSoft">
            {progress?.completed ?? 0} / {progress?.total ?? 0} missions completed
          </div>
        </div>
        <div className="text-4xl font-black text-text">{percent}%</div>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-line/70">
        <div className="h-full rounded-full bg-gradient-to-r from-moss via-neon to-gold shadow-neon transition-all" style={{ width: `${percent}%` }} />
      </div>
    </section>
  );
}
