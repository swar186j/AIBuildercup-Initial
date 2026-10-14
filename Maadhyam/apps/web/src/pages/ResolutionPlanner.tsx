import { useEffect, useState } from "react";
import ReasoningWorkspace from "../components/ReasoningWorkspace";
import { Link } from "react-router-dom";
import { useDocuments } from "../context/DocumentContext";
import { preparePassport, type PassportPlanResponse } from "../services/citizenIntelligence";

export default function ResolutionPlanner() {
  const { documents } = useDocuments();
  const [assessment, setAssessment] = useState<PassportPlanResponse | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    preparePassport(documents)
      .then((result) => { if (active) { setAssessment(result); setError(""); } })
      .catch(() => { if (active) { setAssessment(null); setError("Cannot reach the intelligence API. Start the backend and retry."); } });
    return () => { active = false; };
  }, [documents]);
  const completed = new Set<string>(); // No inferred completion from upload or category.
  const citizen = assessment?.assessment;
  const plan = assessment?.passportPlan;
  return <div className="mx-auto max-w-5xl space-y-6 pb-24 text-[#173f68] dark:text-[#EAF4F7]">
    <header><p className="text-xs font-bold uppercase tracking-widest text-[#087f79] dark:text-[#2FE9C2]">Preparation workspace</p>
      <h1 className="mt-2 text-3xl font-bold">Resolution Planner</h1>
      <p className="mt-2 text-slate-600 dark:text-[#A7BBC8]">A personalized preparation sequence from your reviewed Vault metadata. Not an official checklist or eligibility decision.</p>
    </header>
    <div className="flex flex-wrap gap-3"><Link to="/documents" className="rounded-lg bg-[#167E75] px-4 py-2 font-semibold text-white">Review Vault documents</Link>
      <Link to="/services/passport" className="rounded-lg border border-slate-200 dark:border-[#253947] px-4 py-2 font-semibold text-[#087f79] dark:text-[#2FE9C2]">Passport services</Link></div>
    {error && <p role="alert" className="rounded-lg border border-amber-500/40 p-4 text-amber-800 dark:text-amber-200">{error}</p>}
    {!assessment && !error && <p role="status">Building your plan…</p>}
    {citizen && plan && <>
      <section className="rounded-2xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-5">
        <h2 className="text-xl font-bold text-[#087f79] dark:text-[#2FE9C2]">Your document situation</h2>
        <p className="mt-3">{citizen.documentCount} uploaded · {citizen.reviewedSelfDocuments} reviewed self-held · {citizen.findings.length} potential discrepancies</p>
        <p className="mt-2 text-sm text-slate-600 dark:text-[#A7BBC8]">{citizen.readinessNote}</p>
        {citizen.familyHolders.length > 0 && <p className="mt-2 text-sm text-slate-600 dark:text-[#A7BBC8]">Other document holders: {citizen.familyHolders.join(", ")}. Their documents are not treated as the applicant's identity.</p>}
      </section>
      {citizen.findings.length > 0 && <section className="space-y-3"><h2 className="text-lg font-bold">Items to investigate</h2>
        {citizen.findings.map(f => <article key={f.id} className="rounded-xl border border-amber-500/30 bg-[#edf5f4] dark:bg-[#203440] p-4"><strong className="text-amber-800 dark:text-amber-200">{f.field}</strong><p className="mt-1 text-sm">{f.message}</p></article>)}</section>}
      <section className="space-y-3" aria-label="Passport correction alternatives">
        <h2 className="text-lg font-bold text-[#087f79] dark:text-[#2FE9C2]">Passport correction alternatives</h2>
        {plan.resolutionOptions.length === 0 && <p className="text-sm text-slate-600 dark:text-[#A7BBC8]">No conflicting fields detected in reviewed applicant metadata. This does not establish official acceptance.</p>}
        {plan.resolutionOptions.map(option => <article key={option.findingId} className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4">
          <h3 className="font-semibold">{option.field} — verify before correcting</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-[#A7BBC8]">{option.reason}</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">{option.alternatives.map(alt => <li key={alt.id}>{alt.label}</li>)}</ul>
        </article>)}
        {plan.preparationBlockers.length > 0 && <div className="rounded-xl border border-amber-500/30 p-4" aria-label="Preparation blockers"><h3 className="font-semibold text-amber-800 dark:text-amber-200">Preparation blockers</h3><ul className="mt-2 list-disc pl-5 text-sm">{plan.preparationBlockers.map(blocker => <li key={blocker}>{blocker}</li>)}</ul></div>}
        {plan.nextAction && <p className="rounded-lg border border-slate-200 dark:border-[#253947] p-3 text-sm"><strong>Suggested next action:</strong> {plan.nextAction}</p>}
        <p className="text-xs text-slate-600 dark:text-[#A7BBC8]">{plan.disclaimer}</p>
      </section>
      <section className="space-y-3"><h2 className="text-lg font-bold">Your next steps</h2>
        {([...citizen.tasks].sort((a, b) => { const ai = plan.orderedTaskIds.indexOf(a.id); const bi = plan.orderedTaskIds.indexOf(b.id); return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi); })).map((task, index) => { const blocked = task.dependsOn.some(id => !completed.has(id)); return <article key={task.id} className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4">
          <div className="flex gap-3"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#edf5f4] dark:bg-[#203440] text-[#087f79] dark:text-[#2FE9C2]">{index + 1}</span>
            <div><h3 className="font-bold">{task.title}</h3><p className="mt-1 text-sm text-slate-600 dark:text-[#A7BBC8]">{task.reason}</p>
              {task.dependsOn.length > 0 && <p className="mt-2 text-xs text-[#087f79] dark:text-[#2FE9C2]">Prerequisites: {task.dependsOn.join(", ")}</p>}
              <p className="mt-1 text-xs text-slate-600 dark:text-[#A7BBC8]">{blocked ? "Requires prerequisite review" : "Suggested preparation step"} · Completion is not automatically verified.</p>
            </div></div></article>; })}</section>
      <section className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4 text-sm"><h2 className="font-bold text-[#087f79] dark:text-[#2FE9C2]">What-if simulation</h2>
        <p className="mt-2 text-slate-600 dark:text-[#A7BBC8]">If every detected conflict is resolved, {citizen.whatIf.allConflictsResolved.remainingReviewTasks} review tasks remain in this illustrative scenario. This does not establish application readiness.</p></section>
      <ReasoningWorkspace />
      <a href={citizen.sourceUrl} target="_blank" rel="noopener noreferrer" className="inline-block text-sm font-semibold text-[#087f79] dark:text-[#2FE9C2] underline">Check official Passport Seva guidance ↗</a>
    </>}
  </div>;
}
