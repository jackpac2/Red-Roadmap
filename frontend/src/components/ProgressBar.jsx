export function ProgressBar({ progress }) {
  const percent = progress?.percent ?? 0;
  return (
    <section className="rounded-lg border border-line bg-panel/90 p-4 shadow-panel">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-sm font-black uppercase text-text">Overall Progress</div>
          <div className="text-xs font-semibold text-muted">
            {progress?.completed ?? 0} / {progress?.total ?? 0} missions completed
          </div>
        </div>
        <div className="text-2xl font-black text-neon">{percent}%</div>
      </div>
      <div className="h-3 overflow-hidden rounded-full border border-cyanLine/60 bg-ink">
        <div className="h-full rounded-full bg-gradient-to-r from-neon via-purple-500 to-cyanLine shadow-neon transition-all" style={{ width: `${percent}%` }} />
      </div>
    </section>
  );
}
