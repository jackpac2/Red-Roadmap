import { Check, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

export function StepList({ mission, onAddStep, onCompleteStep, onUpdateStep, onDeleteStep }) {
  const [title, setTitle] = useState("");
  const steps = Array.isArray(mission?.micro_actions) ? mission.micro_actions : [];

  const submit = async (event) => {
    event.preventDefault();
    if (!title.trim()) return;
    await onAddStep(mission.id, title.trim());
    setTitle("");
  };

  return (
    <div className="mt-3 border-t border-line/70 pt-3">
      <div className="space-y-2">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-2 rounded-lg bg-ink/80 px-3 py-2">
            <button onClick={() => onCompleteStep(step.id, !step.completed)} className={`icon-btn ${step.completed ? "text-emerald-300" : "text-muted"}`} title="Complete step">
              <Check size={16} />
            </button>
            <span className={`min-w-0 flex-1 truncate text-sm font-semibold ${step.completed ? "text-muted line-through" : "text-text"}`}>{step?.title || "Untitled step"}</span>
            <button onClick={() => onUpdateStep(step)} className="icon-btn" title="Edit step"><Pencil size={15} /></button>
            <button onClick={() => onDeleteStep(step.id)} className="icon-btn danger" title="Delete step"><Trash2 size={15} /></button>
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="mt-3 flex gap-2">
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Add mission step" className="field" />
        <button className="icon-btn primary" title="Add step"><Plus size={17} /></button>
      </form>
    </div>
  );
}
