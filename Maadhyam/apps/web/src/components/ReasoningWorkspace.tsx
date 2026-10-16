import { useAsyncResource } from "../hooks/useAsyncResource";
import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useDocuments } from '../context/DocumentContext';
import { compareDocuments } from '../utils/documentComparison';
import { reasonCitizen, type FamilyEvidenceLink, type ReasoningResponse, type ReasoningSimulation } from '../services/citizenIntelligence';

type EditableField = 'printedName' | 'dateOfBirth' | 'residentialAddress';
type Journey = 'correction' | 'family';
const fieldLabels: Record<EditableField, string> = {
  printedName: 'Name', dateOfBirth: 'Date of birth', residentialAddress: 'Residential address',
};
const relations: FamilyEvidenceLink['relation'][] = ['parent', 'guardian', 'spouse', 'child', 'sibling', 'other'];
const card = 'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-[#293956] dark:bg-[#162430]';
const input = 'mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm text-slate-900 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20 dark:border-[#385065] dark:bg-[#203440] dark:text-slate-100';
const muted = 'text-sm text-slate-600 dark:text-[#A7BBC8]';

export default function ReasoningWorkspace() {
  const { documents } = useDocuments();
  const [journey, setJourney] = useState<Journey>('correction');
  const [target, setTarget] = useState('');
  const [field, setField] = useState<EditableField>('printedName');
  const [replacement, setReplacement] = useState('');
  const [familyDoc, setFamilyDoc] = useState('');
  const [relation, setRelation] = useState<FamilyEvidenceLink['relation']>('parent');
  const [evidenceIds, setEvidenceIds] = useState<string[]>([]);
  const [links, setLinks] = useState<FamilyEvidenceLink[]>([]);
  const [simulations, setSimulations] = useState<ReasoningSimulation[]>([]);
  const [showTechnical, setShowTechnical] = useState(false);

  const ids = useMemo(() => new Set(documents.map(d => d.id)), [documents]);
  const validLinks = useMemo(() => links.filter(l => ids.has(l.documentId)).map(l => ({
    ...l, relationshipEvidenceDocumentIds: l.relationshipEvidenceDocumentIds.filter(id => ids.has(id)),
  })), [links, ids]);
  const validSimulations = useMemo(() => simulations.filter(s => Object.keys(s.replaceFields || {}).every(id => ids.has(id))), [simulations, ids]);
  const reviewedDocs = documents.filter(d => d.status === 'reviewed' && d.metadata.holder === 'self');
  const familyDocs = documents.filter(d => d.metadata.holder !== 'self');
  const selectedDoc = documents.find(d => d.id === target);
  const currentValue = selectedDoc ? String(selectedDoc.metadata[field] || '') : '';
  const loadReasoning = useCallback(() => reasonCitizen(documents, validLinks, validSimulations), [documents, validLinks, validSimulations]);
  const { data: result, error: loadError, loading: busy } = useAsyncResource<ReasoningResponse>(loadReasoning);
  const error = loadError ? 'Could not analyze your documents. Please check the backend and try again.' : '';

  const sim = result?.simulations.find(s => s.id === 'citizen-what-if');
  const beforeComparison = useMemo(() => compareDocuments(documents), [documents]);
  const afterComparison = useMemo(() => compareDocuments(documents.map(d => d.id === target && simulations.length ? { ...d, metadata: { ...d.metadata, [field]: replacement.trim() } } : d)), [documents, target, field, replacement, simulations]);
  const relatedPairs = afterComparison.comparisons.filter(c => (c.firstId === target || c.secondId === target) && c.field === (field === 'printedName' ? 'name' : field === 'residentialAddress' ? 'address' : 'dateOfBirth'));

  const selectedFamilyDoc = documents.find(d => d.id === familyDoc);

  function runSimulation() {
    if (!target || !replacement.trim()) return;
    setSimulations([{
      id: 'citizen-what-if',
      label: `What if ${fieldLabels[field].toLowerCase()} were corrected?`,
      replaceFields: { [target]: { [field]: replacement.trim() } },
    }]);
  }

  function addFamilyLink() {
    if (!familyDoc || validLinks.some(l => l.documentId === familyDoc)) return;
    setLinks(previous => [...previous, {
      documentId: familyDoc, relation, claimedByApplicant: true,
      relationshipEvidenceDocumentIds: evidenceIds.filter(id => id !== familyDoc),
    }]);
    setEvidenceIds([]);
  }

  return <section className="space-y-5 text-[#173f68] dark:text-[#EAF4F7]" aria-label="Citizen document decision assistant">
    <div className="space-y-2">
      <p className="text-xs font-bold uppercase tracking-widest text-teal-700 dark:text-[#2FE9C2]">Explore your options</p>
      <h2 className="text-2xl font-bold">Find a way forward with your documents</h2>
      <p className={muted}>Choose a situation below. Maadhyam uses your Vault details to explain what to check next—without changing any document.</p>
    </div>

    <div className="grid gap-3 sm:grid-cols-2" role="group" aria-label="Choose a document situation">
      <button type="button" onClick={() => setJourney('correction')} aria-pressed={journey === 'correction'} className={`rounded-2xl border p-4 text-left transition ${journey === 'correction' ? 'border-teal-600 bg-teal-50 ring-2 ring-teal-600/20 dark:border-[#2FE9C2] dark:bg-[#173B40]' : 'border-slate-200 bg-white hover:border-teal-400 dark:border-[#293956] dark:bg-[#162430]'}`}>
        <span className="text-2xl" aria-hidden="true">✏️</span>
        <span className="mt-2 block font-bold">I need to correct a detail</span>
        <span className={`mt-1 block ${muted}`}>See what could change if a name, DOB or address is corrected.</span>
      </button>
      <button type="button" onClick={() => setJourney('family')} aria-pressed={journey === 'family'} className={`rounded-2xl border p-4 text-left transition ${journey === 'family' ? 'border-teal-600 bg-teal-50 ring-2 ring-teal-600/20 dark:border-[#2FE9C2] dark:bg-[#173B40]' : 'border-slate-200 bg-white hover:border-teal-400 dark:border-[#293956] dark:bg-[#162430]'}`}>
        <span className="text-2xl" aria-hidden="true">👨‍👩‍👧</span>
        <span className="mt-2 block font-bold">I have a family member's document</span>
        <span className={`mt-1 block ${muted}`}>Understand what relationship evidence may need checking.</span>
      </button>
    </div>

    {journey === 'correction' ? <div className={card} aria-label="Try a document correction">
      <div className="mb-5 flex items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-100 font-bold text-teal-800 dark:bg-[#245253] dark:text-[#2FE9C2]">1</span>
        <div><h3 className="text-lg font-bold">Try a correction before taking action</h3><p className={muted}>This is a safe preview. Your original Vault document stays unchanged.</p></div></div>
      {reviewedDocs.length === 0 ? <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-[#342B24]">
        <p className="font-semibold">First, review a document in your Vault</p><p className={`mt-1 ${muted}`}>A reviewed applicant-held document is needed for a meaningful comparison.</p>
        <Link to="/documents" className="mt-3 inline-block font-semibold text-teal-700 underline dark:text-[#2FE9C2]">Go to Document Vault →</Link>
      </div> : <div className="grid gap-4">
        <label className="block text-sm font-medium">Which document would you like to check?
          <select aria-label="What-if document" className={input} value={target} onChange={e => { setTarget(e.target.value); setSimulations([]); }}>
            <option value="">Select your document</option>{reviewedDocs.map(d => <option key={d.id} value={d.id}>{d.file.name}</option>)}
          </select></label>
        <label className="block text-sm font-medium">What detail needs correction?
          <select aria-label="What-if field" className={input} value={field} onChange={e => { setField(e.target.value as EditableField); setReplacement(''); setSimulations([]); }}>
            {Object.entries(fieldLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select></label>
        {selectedDoc && <div className="rounded-xl bg-slate-100 p-4 dark:bg-[#203440]"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Current Vault value</p><p className="mt-1 break-words font-medium">{currentValue || 'Not provided in this document'}</p></div>}
        <label className="block text-sm font-medium">What should the corrected value be?
          <input aria-label="Hypothetical value" className={input} value={replacement} onChange={e => setReplacement(e.target.value)} placeholder={field === 'dateOfBirth' ? 'DD/MM/YYYY or YYYY-MM-DD' : 'Enter a hypothetical corrected value'} />
        </label>
        <div className="flex flex-wrap gap-3">
          <button type="button" disabled={!target || !replacement.trim() || busy} onClick={runSimulation} className="rounded-xl bg-[#167E75] px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">{busy ? 'Analyzing…' : 'See the impact →'}</button>
          <button type="button" onClick={() => { setSimulations([]); setReplacement(''); }} className="rounded-xl border border-slate-300 px-4 py-3 font-semibold dark:border-[#496474]">Start over</button>
        </div>
      </div>}
      {sim && <div className="mt-6 space-y-4 border-t border-slate-200 pt-5 dark:border-[#385065]" aria-live="polite">
        <h4 className="text-lg font-bold">Here's what your correction could change</h4>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-[#385065] dark:bg-[#203440]"><p className="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Before</p><p className="mt-2 text-2xl font-bold">{sim.before.reviewFindings.length}</p><p className={muted}>issues needing review</p><p className="mt-2 text-xs">{sim.before.blockers.length} preparation blockers</p></div>
          <div className="rounded-xl border border-teal-300 bg-teal-50 p-4 dark:border-teal-700 dark:bg-[#173B40]"><p className="text-xs font-bold uppercase text-teal-700 dark:text-[#2FE9C2]">After (hypothetical)</p><p className="mt-2 text-2xl font-bold">{sim.after.reviewFindings.length}</p><p className={muted}>issues needing review</p><p className="mt-2 text-xs">{sim.after.blockers.length} preparation blockers</p></div>
        </div>
        {simulations.length > 0 && <div className="rounded-xl border border-teal-300 bg-white p-4 text-slate-900 dark:border-teal-600 dark:bg-[#203440] dark:text-white">
          <h5 className="font-bold">Field-level impact across your uploaded documents</h5>
          <p className="mt-1 text-sm">Before: {beforeComparison.findings.length} differing field pairs · After: {afterComparison.findings.length} differing field pairs. {afterComparison.skippedFieldPairs} comparisons cannot be assessed because data is missing.</p>
          <p className="mt-2 text-sm">{selectedDoc?.file.name}: <strong>{currentValue || 'Missing'}</strong> → <strong>{replacement}</strong></p>
          {relatedPairs.length ? relatedPairs.map((c,i) => <p key={i} className="mt-2 rounded-lg border border-slate-300 p-2 text-sm dark:border-slate-500">{c.firstName} ↔ {c.secondName}: <strong>{c.status === 'match' ? 'Match' : c.status === 'difference' ? 'Mismatch' : 'Missing data'}</strong> · {c.firstValue || 'Missing'} / {c.secondValue || 'Missing'}{c.needsReview ? ' (unreviewed metadata)' : ''}</p>) : <p className="mt-2 text-sm">No other document for this holder has comparable metadata. Upload/review another document to measure cross-document impact.</p>}
          <p className="mt-2 text-xs">The backend counters above use reviewed applicant evidence only; this expanded preview includes provisional unreviewed metadata and does not verify authenticity.</p>
        </div>}
        {sim.resolvedFindingIds.length > 0 && <p className="rounded-xl bg-teal-50 p-3 text-sm text-teal-900 dark:bg-[#173B40] dark:text-[#2FE9C2]">Potentially resolved: {sim.resolvedFindingIds.join(', ')}</p>}
        {sim.newFindingIds.length > 0 && <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900 dark:bg-[#342B24] dark:text-amber-200">New issues to check: {sim.newFindingIds.join(', ')}</p>}
        {sim.resolvedFindingIds.length === 0 && sim.newFindingIds.length === 0 && <p className={muted}>No change in detected review issues. That can happen when the field was not conflicting with other reviewed documents.</p>}
        <p className={muted}>Next: compare the original records and confirm the correct value with the issuing authority before requesting a correction.</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{sim.caution}</p>
      </div>}
    </div> : <div className={card} aria-label="Check family document evidence">
      <div className="mb-5 flex items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-100 font-bold text-teal-800 dark:bg-[#245253] dark:text-[#2FE9C2]">1</span>
        <div><h3 className="text-lg font-bold">Check a family member's document</h3><p className={muted}>We help you organize relationship evidence—not declare that a family document will be accepted.</p></div></div>
      {familyDocs.length === 0 ? <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-[#342B24]">
        <p className="font-semibold">No family-held documents in your Vault yet</p><p className={`mt-1 ${muted}`}>Add a sample document and mark its holder as parent/guardian, spouse or other. Then come back to check the relationship.</p>
        <Link to="/documents" className="mt-3 inline-block font-semibold text-teal-700 underline dark:text-[#2FE9C2]">Add a document in Vault →</Link>
      </div> : <div className="space-y-4">
        <label className="block text-sm font-medium">Which family member's document do you have?
          <select aria-label="Family document" className={input} value={familyDoc} onChange={e => { setFamilyDoc(e.target.value); setEvidenceIds([]); }}>
            <option value="">Choose a family-held document</option>{familyDocs.map(d => <option key={d.id} value={d.id}>{d.file.name}</option>)}
          </select></label>
        <label className="block text-sm font-medium">How is this person related to you?
          <select aria-label="Claimed relationship" className={input} value={relation} onChange={e => setRelation(e.target.value as FamilyEvidenceLink['relation'])}>
            {relations.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
          </select></label>
        <fieldset><legend className="text-sm font-medium">Do you have any documents supporting this relationship? <span className="font-normal text-slate-500">(optional)</span></legend>
          <div className="mt-2 space-y-2">{documents.filter(d => d.id !== familyDoc).map(d => <label key={d.id} className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm dark:border-[#385065]"><input type="checkbox" className="h-4 w-4 accent-teal-700" checked={evidenceIds.includes(d.id)} onChange={e => setEvidenceIds(previous => e.target.checked ? [...previous, d.id] : previous.filter(id => id !== d.id))}/><span className="break-all">{d.file.name}</span></label>)}
            {documents.filter(d => d.id !== familyDoc).length === 0 && <p className={muted}>No additional documents uploaded. You can still check what evidence is missing.</p>}
          </div></fieldset>
        <button type="button" disabled={!familyDoc || validLinks.some(l => l.documentId === familyDoc) || busy} onClick={addFamilyLink} className="rounded-xl bg-[#167E75] px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">Check relationship evidence →</button>
        {selectedFamilyDoc && <p className="text-xs text-slate-500 dark:text-slate-400">Selected: {selectedFamilyDoc.file.name}. Your relationship claim is not official verification.</p>}
      </div>}
      {validLinks.length > 0 && <div className="mt-6 space-y-3 border-t border-slate-200 pt-5 dark:border-[#385065]" aria-live="polite">
        <h4 className="text-lg font-bold">Your family document review</h4>
        {validLinks.map(l => {
          const review = result?.familyEvidence.links.find(x => x.documentId === l.documentId);
          return <div key={l.documentId} className="rounded-xl bg-slate-50 p-4 dark:bg-[#203440]">
            <div className="flex flex-wrap items-start justify-between gap-2"><div><p className="font-semibold">{documents.find(d => d.id === l.documentId)?.file.name}</p><p className={muted}>Relationship claimed: {l.relation}</p></div>
              <button type="button" onClick={() => setLinks(old => old.filter(x => x.documentId !== l.documentId))} className="text-sm font-semibold text-teal-700 underline dark:text-[#2FE9C2]">Remove</button></div>
            <p className="mt-3 text-sm">Supporting documents selected: {l.relationshipEvidenceDocumentIds.length}</p>
            {review && <p className="mt-1 text-sm">Manually reviewed supporting documents: {review.reviewedRelationshipEvidenceIds.length}</p>}
            <p className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/30 dark:bg-[#342B24] dark:text-amber-200">Relationship and proof acceptance still require official verification.</p>
            {review && <p className={`mt-2 ${muted}`}>{review.warning}</p>}
          </div>;
        })}
        <p className={muted}>Next: confirm which relationship and supporting documents are required for your specific Passport Seva scenario.</p>
      </div>}
    </div>}

    {busy && <p role="status" className={muted}>Updating your document analysis…</p>}
    {error && <p role="alert" className="rounded-xl border border-amber-300 p-4 text-sm text-amber-800 dark:border-amber-500/30 dark:text-amber-200">{error}</p>}
    {result && <details className={card} open={showTechnical} onToggle={e => setShowTechnical(e.currentTarget.open)}>
      <summary className="cursor-pointer font-semibold">See your preparation steps and analysis details</summary>
      <p className={`mt-2 ${muted}`}>Recommended sequence based on your reviewed Vault metadata:</p>
      <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm">{result.dependencyGraph.executionOrder.map(id => <li key={id}>{result.dependencyGraph.nodes.find(n => n.id === id)?.title || id}</li>)}</ol>
      <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">{result.dependencyGraph.optimizationScope}</p>
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{result.disclaimer}</p>
    </details>}
  </section>;
}
