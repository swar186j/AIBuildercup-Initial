import { useEffect, useState } from "react";
import ReasoningWorkspace from "../components/ReasoningWorkspace";
import { Link } from "react-router-dom";
import { useDocuments } from "../context/DocumentContext";
import { preparePassport, type PassportPlanResponse } from "../services/citizenIntelligence";

type AdvancedReasoning = {
  identityEvolution?: {
    observedNameVariants: { displayName: string; documentIds: string[] }[];
    variationDetected: boolean; legalNameChangeVerified: boolean;
    nextAction: string; note: string;
  };
  addressContinuity?: {
    addressVariants: { address: string; documentIds: string[] }[];
    differentAddressesDetected: boolean; currentAddressVerified: boolean;
    nextAction: string; note: string;
  };
  visitPreparation?: {
    digitalSubmissionVerified: boolean; governmentVisitEliminated: boolean;
    reviewTaskIdsBeforeVisit: string[]; actions: string[]; note: string;
  };
  minimumCorrectionPath?: {
    selectedTaskIds: string[];
    selectedTaskCount: number;
    totalTaskCount: number;
    optimizationScope: string;
  };
  deadlockAnalysis?: {
    structuralDeadlockDetected: boolean;
    issues: { type: string; taskIds: string[]; message: string }[];
    note: string;
  };
  proofSubstitution?: {
    candidates: { category: string; candidateDocumentIds: string[]; hasMultipleCandidates: boolean; substitutionApproved: boolean; note: string }[];
    officialSubstitutionApproved: boolean;
  };
  deadlineRescue?: {
    targetDate: string | null;
    daysRemaining: number | null;
    urgency: string;
    officialDeadlineVerified: boolean;
    actions: string[];
    note?: string;
  };
};

const panel = "rounded-xl border border-slate-200 bg-white p-4 dark:border-[#253947] dark:bg-[#162430]";
const muted = "text-sm text-slate-600 dark:text-[#A7BBC8]";

export default function ResolutionPlanner() {
  const { documents } = useDocuments();
  const [assessment, setAssessment] = useState<PassportPlanResponse | null>(null);
  const [error, setError] = useState("");
  const [advanced, setAdvanced] = useState<AdvancedReasoning | null>(null);
  const [advancedError, setAdvancedError] = useState("");
  const [targetDate, setTargetDate] = useState("");

  useEffect(() => {
    let active = true;
    preparePassport(documents)
      .then((result) => { if (active) { setAssessment(result); setError(""); } })
      .catch(() => { if (active) { setAssessment(null); setError("Cannot reach the intelligence API. Start the backend and retry."); } });
    return () => { active = false; };
  }, [documents]);

  useEffect(() => {
    let active = true;
    setAdvanced(null);
    setAdvancedError("");
    // Send only reviewed metadata and document descriptors, never document bytes.
    const payload = documents.map(d => ({
      id: d.id,
      documentType: d.metadata.documentType || "",
      holder: d.metadata.holder,
      reviewed: d.status === "reviewed",
      categories: d.metadata.categories?.length ? d.metadata.categories : [d.metadata.category],
      printedName: d.metadata.printedName || "",
      dateOfBirth: d.metadata.dateOfBirth || "",
      residentialAddress: d.metadata.residentialAddress || "",
    }));
    fetch("/api/intelligence/reasoning", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documents: payload, targetDate: targetDate || null }),
    })
      .then(async response => {
        if (!response.ok) throw new Error(`Reasoning API returned ${response.status}`);
        return response.json() as Promise<AdvancedReasoning>;
      })
      .then(result => { if (active) setAdvanced(result); })
      .catch(() => { if (active) setAdvancedError("Advanced reasoning could not be loaded. Check the backend and retry."); });
    return () => { active = false; };
  }, [documents, targetDate]);

  const completed = new Set<string>(); // No inferred completion from upload or category.
  const citizen = assessment?.assessment;
  const plan = assessment?.passportPlan;
  const taskNames = new Map(citizen?.tasks.map(t => [t.id, t.title]) ?? []);

  return <div className="mx-auto max-w-5xl space-y-6 pb-24 text-[#173f68] dark:text-[#EAF4F7]">
    <header>
      <p className="text-xs font-bold uppercase tracking-widest text-[#087f79] dark:text-[#2FE9C2]">Preparation workspace</p>
      <h1 className="mt-2 text-3xl font-bold">Resolution Planner</h1>
      <p className="mt-2 text-slate-600 dark:text-[#A7BBC8]">A personalized preparation sequence from your reviewed Vault metadata. Not an official checklist or eligibility decision.</p>
    </header>
    <div className="flex flex-wrap gap-3">
      <Link to="/documents" className="rounded-lg bg-[#167E75] px-4 py-2 font-semibold text-white">Review Vault documents</Link>
      <Link to="/services/passport" className="rounded-lg border border-slate-200 px-4 py-2 font-semibold text-[#087f79] dark:border-[#253947] dark:text-[#2FE9C2]">Passport services</Link>
    </div>
    {error && <p role="alert" className="rounded-lg border border-amber-500/40 p-4 text-amber-800 dark:text-amber-200">{error}</p>}
    {!assessment && !error && <p role="status">Building your plan…</p>}
    {citizen && plan && <>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-[#253947] dark:bg-[#162430]">
        <h2 className="text-xl font-bold text-[#087f79] dark:text-[#2FE9C2]">Your document situation</h2>
        <p className="mt-3">{citizen.documentCount} uploaded · {citizen.reviewedSelfDocuments} reviewed self-held · {citizen.findings.length} potential discrepancies</p>
        <p className={`mt-2 ${muted}`}>{citizen.readinessNote}</p>
        {citizen.familyHolders.length > 0 && <p className={`mt-2 ${muted}`}>Other document holders: {citizen.familyHolders.join(", ")}. Their documents are not treated as the applicant's identity.</p>}
      </section>
      {citizen.findings.length > 0 && <section className="space-y-3">
        <h2 className="text-lg font-bold">Items to investigate</h2>
        {citizen.findings.map(f => <article key={f.id} className="rounded-xl border border-amber-500/30 bg-[#edf5f4] p-4 dark:bg-[#203440]"><strong className="text-amber-800 dark:text-amber-200">{f.field}</strong><p className="mt-1 text-sm">{f.message}</p></article>)}
      </section>}
      <section className="space-y-3" aria-label="Passport correction alternatives">
        <h2 className="text-lg font-bold text-[#087f79] dark:text-[#2FE9C2]">Passport correction alternatives</h2>
        {plan.resolutionOptions.length === 0 && <p className={muted}>No conflicting fields detected in reviewed applicant metadata. This does not establish official acceptance.</p>}
        {plan.resolutionOptions.map(option => <article key={option.findingId} className={panel}>
          <h3 className="font-semibold">{option.field} — verify before correcting</h3>
          <p className={`mt-2 ${muted}`}>{option.reason}</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">{option.alternatives.map(alt => <li key={alt.id}>{alt.label}</li>)}</ul>
        </article>)}
        {plan.preparationBlockers.length > 0 && <div className="rounded-xl border border-amber-500/30 p-4" aria-label="Preparation blockers"><h3 className="font-semibold text-amber-800 dark:text-amber-200">Preparation blockers</h3><ul className="mt-2 list-disc pl-5 text-sm">{plan.preparationBlockers.map(blocker => <li key={blocker}>{blocker}</li>)}</ul></div>}
        {plan.nextAction && <p className="rounded-lg border border-slate-200 p-3 text-sm dark:border-[#253947]"><strong>Suggested next action:</strong> {plan.nextAction}</p>}
        <p className={`text-xs text-slate-600 dark:text-[#A7BBC8]`}>{plan.disclaimer}</p>
      </section>
      <section className="space-y-3"><h2 className="text-lg font-bold">Your next steps</h2>
        {([...citizen.tasks].sort((a, b) => { const ai = plan.orderedTaskIds.indexOf(a.id); const bi = plan.orderedTaskIds.indexOf(b.id); return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi); })).map((task, index) => { const blocked = task.dependsOn.some(id => !completed.has(id)); return <article key={task.id} className={panel}>
          <div className="flex gap-3"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#edf5f4] text-[#087f79] dark:bg-[#203440] dark:text-[#2FE9C2]">{index + 1}</span>
            <div><h3 className="font-bold">{task.title}</h3><p className={`mt-1 ${muted}`}>{task.reason}</p>
              {task.dependsOn.length > 0 && <p className="mt-2 text-xs text-[#087f79] dark:text-[#2FE9C2]">Prerequisites: {task.dependsOn.join(", ")}</p>}
              <p className="mt-1 text-xs text-slate-600 dark:text-[#A7BBC8]">{blocked ? "Requires prerequisite review" : "Suggested preparation step"} · Completion is not automatically verified.</p>
            </div></div></article>; })}
      </section>
      <section className="rounded-2xl border border-teal-300 bg-white p-5 text-slate-900 dark:border-teal-700 dark:bg-[#162430] dark:text-white" aria-label="Your deadline and action plan">
        <h2 className="text-xl font-bold">Your deadline and action plan</h2>
        <label htmlFor="planning-date" className="mt-3 block text-sm">When do you want your documents ready? (Your target, not a government deadline)</label>
        <input id="planning-date" type="date" value={targetDate} onChange={e => setTargetDate(e.target.value)} className="mt-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900" />
        {targetDate && <p className="mt-3 text-sm">{Math.ceil((new Date(`${targetDate}T23:59:59`).getTime()-Date.now())/86400000)} day(s) until your personal target. This does not predict official processing time.</p>}
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm">
          <li>Review the {documents.filter(d => d.status !== 'reviewed').length} unreviewed uploaded document(s) in Vault.</li>
          <li>Fill missing name, DOB and address metadata where it appears on each document.</li>
          <li>Compare the records; investigate differences using original documents and issuing authorities.</li>
          <li>Confirm accepted proofs and appointment requirements on the official Passport Seva website.</li>
          <li>Re-run this planner after reviewing evidence; unresolved blockers remain visible below.</li>
        </ol>
      </section>
      <section className="space-y-4" aria-label="Advanced preparation intelligence">
        <div>
          <h2 className="text-xl font-bold text-[#087f79] dark:text-[#2FE9C2]">Advanced preparation intelligence</h2>
          <p className={`mt-1 ${muted}`}>Deterministic planning from Vault metadata; no official document acceptance or government processing time is inferred.</p>
        </div>
        {advancedError && <p role="alert" className="rounded-lg border border-amber-500/30 p-3 text-amber-800 dark:text-amber-200">{advancedError}</p>}
        {!advanced && !advancedError && <p role="status" className={muted}>Analyzing task dependencies and evidence options…</p>}
        {advanced && <>
          {advanced.minimumCorrectionPath && <article className={panel} aria-label="Minimum prerequisite review path">
            <h3 className="font-bold">Minimum prerequisite review path</h3>
            <p className={`mt-2 ${muted}`}>{advanced.minimumCorrectionPath.selectedTaskCount} of {advanced.minimumCorrectionPath.totalTaskCount} preparation tasks selected for critical review.</p>
            {advanced.minimumCorrectionPath.selectedTaskIds.length > 0 ? <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm">{advanced.minimumCorrectionPath.selectedTaskIds.map(id => <li key={id}>{taskNames.get(id) ?? id}</li>)}</ol> : <p className={`mt-2 ${muted}`}>No priority-1 review tasks identified.</p>}
            <p className="mt-3 text-xs text-slate-600 dark:text-[#A7BBC8]">{advanced.minimumCorrectionPath.optimizationScope}</p>
          </article>}
          {advanced.deadlockAnalysis && <article className={panel} aria-label="Dependency diagnostics">
            <h3 className="font-bold">Dependency diagnostics</h3>
            {advanced.deadlockAnalysis.structuralDeadlockDetected ? <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-amber-800 dark:text-amber-200">{advanced.deadlockAnalysis.issues.map((issue, i) => <li key={`${issue.type}-${i}`}>{issue.message} ({issue.taskIds.join(", ")})</li>)}</ul> : <p className={`mt-2 ${muted}`}>No structural dependency cycles or missing prerequisites detected.</p>}
            <p className="mt-3 text-xs text-slate-600 dark:text-[#A7BBC8]">{advanced.deadlockAnalysis.note}</p>
          </article>}
          {advanced.proofSubstitution && <article className={panel} aria-label="Alternative evidence candidates">
            <h3 className="font-bold">Alternative evidence candidates</h3>
            <div className="mt-3 space-y-3">{advanced.proofSubstitution.candidates.map(candidate => <div key={candidate.category} className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-[#345061] dark:bg-[#203440]">
              <h4 className="font-semibold capitalize">{candidate.category}</h4>
              <p className={`mt-1 ${muted}`}>{candidate.candidateDocumentIds.length ? `${candidate.candidateDocumentIds.length} reviewed self-held candidate(s): ${candidate.candidateDocumentIds.map(id => documents.find(d => d.id === id)?.file.name ?? id).join(", ")}` : "No reviewed self-held candidates found."}</p>
              {candidate.hasMultipleCandidates && <p className="mt-1 text-xs text-teal-700 dark:text-[#2FE9C2]">Multiple candidates to investigate</p>}
            </div>)}</div>
            <p className="mt-3 text-xs text-slate-600 dark:text-[#A7BBC8]">Candidate categories do not establish interchangeability or official acceptance.</p>
          </article>}
          {advanced.identityEvolution && <article className={panel} aria-label="Identity name variations">
            <h3 className="font-bold">Are your names consistent across documents?</h3>
            <p className={`mt-2 ${muted}`}>{advanced.identityEvolution.variationDetected ? "Different name values were found in reviewed applicant documents." : "No different name values detected among reviewed applicant documents."}</p>
            {advanced.identityEvolution.observedNameVariants.map((item, i) => <p key={i} className="mt-2 text-sm"><strong>{item.displayName}</strong> · {item.documentIds.length} reviewed document(s)</p>)}
            <p className="mt-3 text-sm">{advanced.identityEvolution.nextAction}</p>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{advanced.identityEvolution.note}</p>
          </article>}
          {advanced.addressContinuity && <article className={panel} aria-label="Address consistency">
            <h3 className="font-bold">Which address should you review?</h3>
            <p className={`mt-2 ${muted}`}>{advanced.addressContinuity.differentAddressesDetected ? "Different addresses appear in reviewed applicant documents." : "No different addresses detected among reviewed applicant documents."}</p>
            {advanced.addressContinuity.addressVariants.map((item, i) => <p key={i} className="mt-2 break-words text-sm"><strong>{item.address}</strong> · {item.documentIds.length} document(s)</p>)}
            <p className="mt-3 text-sm">{advanced.addressContinuity.nextAction}</p>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{advanced.addressContinuity.note}</p>
          </article>}
          {advanced.visitPreparation && <article className={panel} aria-label="Visit preparation">
            <h3 className="font-bold">Avoid an unnecessary repeat visit</h3>
            <p className={`mt-2 ${muted}`}>Check what you need before visiting an office. We cannot confirm that a government visit can be skipped.</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">{advanced.visitPreparation.actions.map((action, i) => <li key={i}>{action}</li>)}</ul>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{advanced.visitPreparation.note}</p>
          </article>}
          <article className={panel} aria-label="Deadline planning">
            <h3 className="font-bold">Deadline planning</h3>
            <p className={`mt-2 ${muted}`}>Set your target date in the action plan above.</p>
            {advanced.deadlineRescue && <div className="mt-3 space-y-2">
              <p className="text-sm">Urgency: <strong>{advanced.deadlineRescue.urgency.replaceAll("-", " ")}</strong>{advanced.deadlineRescue.daysRemaining !== null ? ` · ${advanced.deadlineRescue.daysRemaining} day(s) until target` : ""}</p>
              <ul className="list-disc space-y-1 pl-5 text-sm">{advanced.deadlineRescue.actions.map((action, i) => <li key={i}>{action}</li>)}</ul>
              <p className="text-xs text-slate-600 dark:text-[#A7BBC8]">{advanced.deadlineRescue.note ?? "Confirm the actual deadline with the relevant authority."}</p>
            </div>}
          </article>
        </>}
      </section>

      <ReasoningWorkspace />
      <a href={citizen.sourceUrl} target="_blank" rel="noopener noreferrer" className="inline-block text-sm font-semibold text-[#087f79] underline dark:text-[#2FE9C2]">Check official Passport Seva guidance ↗</a>
    </>}
  </div>;
}
