import {Link} from 'react-router-dom';
import {useDocuments} from '../context/DocumentContext';
import {useHousehold} from '../context/HouseholdContext';
import {useWorkspace} from '../context/WorkspaceContext';
import {applicantEvidence} from '../utils/applicantEvidence';
import {compareDocuments} from '../utils/documentComparison';

export default function PreparationJourneyProgress({readinessComplete}:{readinessComplete?:boolean}){
 const {documents}=useDocuments();const {members}=useHousehold();
 const {applications,activeCloudPreparationId,plannerCompleted}=useWorkspace();
 const record=applications.find(a=>a.id===activeCloudPreparationId)??applications.find(a=>a.journey);
 const selected=record?.journey;
 const ids=new Set(members.map(m=>m.id));
 const evidence=applicantEvidence(selected?documents.filter(d=>selected.documentIds.includes(d.id)):documents,selected?.applicantHouseholdMemberId,ids);
 const comparison=compareDocuments(evidence,ids);
 const meaningful=comparison.comparisons.filter(c=>c.status!=='missing'&&!c.needsReview);
 const journeyPath=selected?`/services/passport/journey?preparation=${encodeURIComponent(record!.id)}`:'/services/passport/journey';
 const stages=[
  {label:'Discover',path:'/services',done:false},
  {label:'Select service',path:'/services/passport',done:!!selected},
  {label:'Upload',path:'/documents',done:documents.length>0},
  {label:'Extract & review',path:'/documents',done:evidence.length>0&&evidence.every(d=>d.status==='reviewed')},
  {label:'Detect issues',path:'/documents',done:meaningful.length>0&&comparison.skippedFieldPairs===0},
  {label:'Plan corrections',path:'/planner',done:plannerCompleted.includes('differences')},
  {label:'Check readiness',path:journeyPath,done:readinessComplete===true},
  {label:'Saved next steps',path:'/applications',done:!!selected?.lastSavedAt&&selected.stepIndex===3},
 ];
 return <nav aria-label="Connected preparation journey" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-[#173f68] dark:border-[#293956] dark:bg-[#18243B] dark:text-slate-100"><p className="font-semibold">Your connected preparation journey</p><ol className="mt-3 flex flex-wrap gap-2">{stages.map((s,i)=><li key={s.label}><Link to={s.path} className={`inline-flex rounded-lg border px-3 py-2 ${s.done?'border-teal-400 bg-teal-50 text-teal-900 dark:bg-teal-950 dark:text-teal-100':'border-slate-200 dark:border-slate-600'}`}><span className="mr-1" aria-hidden="true">{s.done?'✓':i+1+'.'}</span>{s.label}{s.done&&<span className="sr-only"> — completed workspace action</span>}</Link></li>)}</ol><p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Marks reflect recorded actions and current evidence. Use any step freely. Readiness is calculated in the Passport journey; no government submission or verification is tracked here.</p></nav>;
}
