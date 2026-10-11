import { useMemo, useState } from "react";
import { useWorkspace, plannerTasks } from "../context/WorkspaceContext";
import { Link } from "react-router-dom";
import { AlertCircle, ArrowRight, CheckCircle2, ClipboardList, FileText, RotateCcw, ShieldCheck } from "lucide-react";
import { useDocuments } from "../context/DocumentContext";

export default function ResolutionPlanner() {
  const { documents } = useDocuments();
  const { plannerCompleted: completed, togglePlannerTask, resetPlanner } = useWorkspace();
  const tasks = plannerTasks;
  const [showAll, setShowAll] = useState(true);
  const [notice, setNotice] = useState("");
  const completeSet = useMemo(() => new Set(completed), [completed]);
  const readyCount = tasks.filter((task) => !completeSet.has(task.id) && task.dependsOn.every((id) => completeSet.has(id))).length;
  const progress = Math.round((completed.length / tasks.length) * 100);
  const nextTask = tasks.find((task) => !completeSet.has(task.id) && task.dependsOn.every((id) => completeSet.has(id)));

  function toggleTask(id: string) {
    if (completeSet.has(id)) {
      setNotice("Step reopened. Dependent steps were reopened as well.");
    } else {
      setNotice("Marked complete for this demo session. No government status was changed.");
    }
    togglePlannerTask(id);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-7 pb-24">
      <header>
        <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">Preparation workspace</p>
        <h1 className="mt-2 text-3xl font-bold text-[#173f68]">Resolution Planner</h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">Follow a practical sequence for reviewing documents and planning your next steps. This demo plan is illustrative, not an official passport checklist.</p>
      </header>

      <div className="rounded-xl border border-[#cde5e3] bg-[#f2f8f8] px-4 py-3 text-sm leading-6 text-[#173f68]">
        <strong>Frontend demo:</strong> Tasks are marked manually. Document uploads do not automatically complete tasks, and progress resets on refresh. No government system is connected.
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Steps completed", value: `${completed.length}/${tasks.length}`, icon: CheckCircle2 },
          { label: "Ready to work on", value: readyCount, icon: ClipboardList },
          { label: "Files in your Vault", value: documents.length, icon: FileText },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between text-sm font-medium text-slate-600"><span>{label}</span><Icon size={20} className="text-[#147d83]" /></div>
            <p className="mt-4 text-3xl font-bold text-[#173f68]">{value}</p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-[#173f68]">Your preparation plan</h2>
            <p className="mt-1 text-sm text-slate-500">Complete prerequisite steps before marking later steps done.</p>
          </div>
          <button type="button" onClick={() => { resetPlanner(); setNotice("Demo plan reset."); }} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-[#173f68] hover:bg-slate-50"><RotateCcw size={16} /> Reset plan</button>
        </div>
        <div className="mt-5 flex items-center justify-between text-sm"><span className="font-medium text-slate-600">Overall progress</span><span className="font-bold text-[#173f68]">{progress}%</span></div>
        <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-label="Preparation plan progress" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-full rounded-full bg-[#147d83] transition-all" style={{ width: `${progress}%` }} />
        </div>
        {notice && <p role="status" className="mt-3 text-sm text-[#147d83]">{notice}</p>}
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-600">{nextTask ? <>Next suggested step: <strong className="text-[#173f68]">{nextTask.title}</strong></> : <strong className="text-[#173f68]">All demo steps completed.</strong>}</p>
          <button type="button" onClick={() => setShowAll((previous) => !previous)} className="text-sm font-semibold text-[#147d83] hover:underline">{showAll ? "Show actionable steps" : "Show all steps"}</button>
        </div>

        <ol className="mt-6 space-y-4">
          {tasks.filter((task) => showAll || completeSet.has(task.id) || task.dependsOn.every((id) => completeSet.has(id))).map((task) => {
            const done = completeSet.has(task.id);
            const unlocked = task.dependsOn.every((id) => completeSet.has(id));
            const blockers = task.dependsOn.filter((id) => !completeSet.has(id)).map((id) => tasks.find((item) => item.id === id)?.title).filter(Boolean);
            return (
              <li key={task.id} className={`rounded-2xl border p-4 sm:p-5 ${done ? "border-[#cde5e3] bg-[#f4faf9]" : unlocked ? "border-slate-200 bg-white" : "border-slate-200 bg-slate-50"}`}>
                <div className="flex items-start gap-3">
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold ${done ? "bg-[#147d83] text-white" : "bg-slate-200 text-[#173f68]"}`}>{done ? <CheckCircle2 size={20} /> : tasks.indexOf(task) + 1}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-bold text-[#173f68]">{task.title}</h3>
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${done ? "bg-emerald-100 text-emerald-800" : unlocked ? "bg-blue-50 text-blue-800" : "bg-amber-50 text-amber-800"}`}>{done ? "Done" : unlocked ? "Ready" : "Blocked"}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{task.description}</p>
                    {blockers.length > 0 && <p className="mt-3 flex items-start gap-2 text-xs text-amber-800"><AlertCircle size={15} className="mt-0.5 shrink-0" /> First complete: {blockers.join(", ")}</p>}
                    <div className="mt-4 flex flex-wrap items-center gap-4">
                      <button type="button" disabled={!done && !unlocked} onClick={() => toggleTask(task.id)} className="rounded-xl bg-[#147d83] px-4 py-2.5 text-xs font-semibold text-white hover:bg-[#126a70] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600">{done ? "Reopen step" : "Mark step done"}</button>
                      <Link to={task.href} className="inline-flex items-center gap-1.5 text-sm font-semibold text-[#147d83] hover:underline">{task.action} <ArrowRight size={15} /></Link>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </section>

      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-xs leading-6 text-slate-600">
        <ShieldCheck size={19} className="mt-0.5 shrink-0 text-[#147d83]" />
        <p>Maadhyam is an independent preparation assistant. Completing this planner does not confirm document validity, eligibility, submission or government approval. Check the current official instructions before acting.</p>
      </div>
    </div>
  );
}
