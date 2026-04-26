import { Filter, Search } from "lucide-react";

export function FilterBar({ query, setQuery, status, setStatus, priority, setPriority }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-line bg-panel p-3 shadow-panel xl:flex-row xl:items-center">
      <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-cyanLine/50 bg-ink px-3 py-2">
        <Search size={17} className="text-neon" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search missions"
          className="min-w-0 flex-1 bg-transparent text-sm font-semibold text-text outline-none placeholder:text-muted"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Filter size={18} className="mt-2 text-muted" />
        <select value={status} onChange={(event) => setStatus(event.target.value)} className="control">
          <option value="ALL">All status</option>
          <option value="PENDING">Pending</option>
          <option value="ACTIVE">Active</option>
          <option value="AWAY">Away</option>
          <option value="COMPLETED">Completed</option>
        </select>
        <select value={priority} onChange={(event) => setPriority(event.target.value)} className="control">
          <option value="ALL">All priority</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>
    </div>
  );
}
