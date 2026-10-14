import { useEffect, useMemo, useState } from 'react';
import { useDocuments } from '../context/DocumentContext';
import { reasonCitizen, type FamilyEvidenceLink, type ReasoningResponse, type ReasoningSimulation } from '../services/citizenIntelligence';

type EditableField = 'printedName' | 'dateOfBirth' | 'residentialAddress';
const fieldLabels: Record<EditableField, string> = {printedName:'Printed name',dateOfBirth:'Date of birth',residentialAddress:'Residential address'};
const relations: FamilyEvidenceLink['relation'][] = ['parent','guardian','spouse','child','sibling','other'];

export default function ReasoningWorkspace() {
  const { documents } = useDocuments();
  const [result, setResult] = useState<ReasoningResponse | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [target, setTarget] = useState('');
  const [field, setField] = useState<EditableField>('printedName');
  const [replacement, setReplacement] = useState('');
  const [familyDoc, setFamilyDoc] = useState('');
  const [relation, setRelation] = useState<FamilyEvidenceLink['relation']>('parent');
  const [evidenceIds, setEvidenceIds] = useState<string[]>([]);
  const [links, setLinks] = useState<FamilyEvidenceLink[]>([]);
  const [simulation, setSimulation] = useState<ReasoningSimulation[]>([]);
  const ids = useMemo(() => new Set(documents.map(d => d.id)), [documents]);
  const validLinks = useMemo(() => links.filter(l => ids.has(l.documentId)).map(l => ({...l,relationshipEvidenceDocumentIds:l.relationshipEvidenceDocumentIds.filter(id=>ids.has(id))})), [links, ids]);
  const validSimulations = useMemo(() => simulation.filter(s => Object.keys(s.replaceFields || {}).every(id=>ids.has(id))), [simulation, ids]);
  const familyDocs = documents.filter(d => d.metadata.holder !== 'self');
  const reviewedDocs = documents.filter(d => d.status === 'reviewed' && d.metadata.holder === 'self');

  useEffect(() => {
    let active = true;
    setBusy(true);
    setResult(null);
    reasonCitizen(documents, validLinks, validSimulations).then(data => {
      if (active) {setResult(data);setError('');}
    }).catch(() => {if(active){setResult(null);setError('Reasoning API unavailable. Please check the backend and retry.');}})
      .finally(()=>{if(active)setBusy(false);});
    return () => {active = false;};
  }, [documents, validLinks, validSimulations]);

  function addSimulation() {
    if (!target || !replacement.trim()) return;
    setSimulation([{id:'what-if-1',label:`What if ${fieldLabels[field]} changed?`,replaceFields:{[target]:{[field]:replacement.trim()}}}]);
  }
  function addFamilyLink() {
    if (!familyDoc || validLinks.some(l=>l.documentId===familyDoc)) return;
    setLinks(previous => [...previous, {documentId:familyDoc,relation,claimedByApplicant:true,relationshipEvidenceDocumentIds:evidenceIds.filter(id=>id!==familyDoc)}]);
    setEvidenceIds([]);
  }
  return <section className="space-y-6 text-[#173f68] dark:text-[#EAF4F7]" aria-label="Advanced reasoning and family evidence">
    <header><h2 className="text-xl font-bold text-[#087f79] dark:text-[#2FE9C2]">What-if Lab & Family Evidence</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-[#A7BBC8]">Explore hypothetical changes and claimed family links. No official records are changed or relationships verified.</p></header>
    <div className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4 space-y-3" aria-label="What-if editor">
      <h3 className="font-semibold">M7 — Try a hypothetical correction</h3>
      <label className="block text-sm">Reviewed applicant document
        <select aria-label="What-if document" className="mt-1 block w-full rounded border border-slate-300 dark:border-[#304653] bg-white dark:bg-[#203440] text-[#173f68] dark:text-[#EAF4F7] p-2" value={target} onChange={e=>setTarget(e.target.value)}>
          <option value="">Choose a document</option>{reviewedDocs.map(d=><option key={d.id} value={d.id}>{d.file.name}</option>)}
        </select></label>
      <label className="block text-sm">Field
        <select aria-label="What-if field" className="mt-1 block w-full rounded border border-slate-300 dark:border-[#304653] bg-white dark:bg-[#203440] text-[#173f68] dark:text-[#EAF4F7] p-2" value={field} onChange={e=>setField(e.target.value as EditableField)}>
          {Object.entries(fieldLabels).map(([key,label])=><option key={key} value={key}>{label}</option>)}
        </select></label>
      <label className="block text-sm">Hypothetical value
        <input aria-label="Hypothetical value" className="mt-1 block w-full rounded border border-slate-300 dark:border-[#304653] bg-white dark:bg-[#203440] text-[#173f68] dark:text-[#EAF4F7] p-2" value={replacement} onChange={e=>setReplacement(e.target.value)} placeholder="Fictional corrected value" /></label>
      <div className="flex flex-wrap gap-2"><button type="button" disabled={!target || !replacement.trim()} onClick={addSimulation} className="rounded bg-[#167E75] px-4 py-2 font-semibold text-white disabled:opacity-40">Run what-if</button>
        <button type="button" onClick={()=>setSimulation([])} className="rounded border border-slate-300 dark:border-[#496474] px-4 py-2 text-[#173f68] dark:text-[#EAF4F7]">Clear simulation</button></div>
      {reviewedDocs.length===0 && <p className="text-amber-800 dark:text-amber-200 text-sm">Review a self-held document in Vault to run a what-if.</p>}
    </div>
    <div className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4 space-y-3" aria-label="Family relationship editor">
      <h3 className="font-semibold">M8 — Claim a family relationship</h3>
      <label className="block text-sm">Family-held document
        <select aria-label="Family document" className="mt-1 block w-full rounded border border-slate-300 dark:border-[#304653] bg-white dark:bg-[#203440] text-[#173f68] dark:text-[#EAF4F7] p-2" value={familyDoc} onChange={e=>setFamilyDoc(e.target.value)}>
          <option value="">Choose a document</option>{familyDocs.map(d=><option key={d.id} value={d.id}>{d.file.name}</option>)}
        </select></label>
      <label className="block text-sm">Claimed relationship
        <select aria-label="Claimed relationship" className="mt-1 block w-full rounded border border-slate-300 dark:border-[#304653] bg-white dark:bg-[#203440] text-[#173f68] dark:text-[#EAF4F7] p-2" value={relation} onChange={e=>setRelation(e.target.value as FamilyEvidenceLink['relation'])}>
          {relations.map(r=><option key={r} value={r}>{r}</option>)}
        </select></label>
      <fieldset><legend className="text-sm">Supporting evidence (optional; not proof of validity)</legend>
        {documents.filter(d=>d.id!==familyDoc).map(d=><label key={d.id} className="flex gap-2 items-center text-sm mt-2"><input type="checkbox" checked={evidenceIds.includes(d.id)} onChange={e=>setEvidenceIds(previous=>e.target.checked?[...previous,d.id]:previous.filter(id=>id!==d.id))}/>{d.file.name}</label>)}</fieldset>
      <button type="button" disabled={!familyDoc || validLinks.some(l=>l.documentId===familyDoc)} onClick={addFamilyLink} className="rounded bg-[#167E75] px-4 py-2 font-semibold text-white disabled:opacity-40">Add family link</button>
      {validLinks.map(l=><div key={l.documentId} className="flex justify-between items-center gap-3 text-sm"><span>{documents.find(d=>d.id===l.documentId)?.file.name} — {l.relation} (claimed, unverified)</span><button type="button" onClick={()=>setLinks(old=>old.filter(x=>x.documentId!==l.documentId))} className="text-[#087f79] dark:text-[#2FE9C2] underline">Remove link</button></div>)}
    </div>
    {busy && <p role="status">Analyzing scenarios…</p>}
    {error && <p role="alert" className="text-amber-800 dark:text-amber-200">{error}</p>}
    {result && <div className="space-y-4" aria-label="Reasoning results">
      <section className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4"><h3 className="font-bold">Baseline</h3><p className="text-sm mt-2">Review findings: {result.baseline.reviewFindings.length} · Blockers: {result.baseline.blockers.length}</p>
        {result.baseline.reviewFindings.map(f=><p key={f} className="text-sm text-amber-800 dark:text-amber-200">{f}</p>)}</section>
      {result.simulations.map(s=><section key={s.id} className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4" aria-label="What-if comparison"><h3 className="font-bold">{s.label}</h3>
        <p className="mt-2 text-sm">Before: {s.before.reviewFindings.length} findings / {s.before.blockers.length} blockers</p>
        <p className="text-sm">After: {s.after.reviewFindings.length} findings / {s.after.blockers.length} blockers</p>
        <p className="text-sm">Resolved: {s.resolvedFindingIds.length} · New: {s.newFindingIds.length}</p>
        {s.resolvedFindingIds.map(f=><p key={f} className="text-sm text-[#087f79] dark:text-[#2FE9C2]">Resolved finding: {f}</p>)}
        {s.newFindingIds.map(f=><p key={f} className="text-sm text-amber-800 dark:text-amber-200">New finding: {f}</p>)}
        <p className="mt-2 text-xs text-slate-600 dark:text-[#A7BBC8]">{s.caution}</p></section>)}
      <section className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4" aria-label="Dependency graph"><h3 className="font-bold">Dependency-safe task sequence</h3>
        <ol className="mt-2 list-decimal pl-5 text-sm space-y-1">{result.dependencyGraph.executionOrder.map(id=><li key={id}>{result.dependencyGraph.nodes.find(n=>n.id===id)?.title || id}</li>)}</ol>
        <p className="mt-2 text-xs text-slate-600 dark:text-[#A7BBC8]">{result.dependencyGraph.optimizationScope}</p></section>
      <section className="rounded-xl border border-slate-200 dark:border-[#253947] bg-white dark:bg-[#162430] p-4" aria-label="Family evidence results"><h3 className="font-bold">Family evidence review</h3>
        {result.familyEvidence.links.map(l=><p key={l.documentId} className="mt-2 text-sm">{documents.find(d=>d.id===l.documentId)?.file.name}: {l.relation}; supporting documents: {l.relationshipEvidenceIds.length}. {l.warning}</p>)}
        {result.familyEvidence.unlinkedFamilyDocumentIds.length>0 && <p className="mt-2 text-sm text-amber-800 dark:text-amber-200">Unlinked family documents: {result.familyEvidence.unlinkedFamilyDocumentIds.length}</p>}
        <p className="mt-2 text-sm text-amber-800 dark:text-amber-200">Official relationship verified: No</p></section>
      <p className="text-xs text-slate-600 dark:text-[#A7BBC8]">{result.disclaimer}</p>
    </div>}
  </section>;
}
