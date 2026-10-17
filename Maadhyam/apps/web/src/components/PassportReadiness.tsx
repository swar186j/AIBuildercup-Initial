import {Link} from 'react-router-dom';
import type {PassportAssessment} from '../services/passportAssessment';
export default function PassportReadiness({assessment,filenames}:{assessment:PassportAssessment;filenames:Map<string,string>}){
 const readiness=assessment.readiness;
 if(!readiness)return <p role="status" className="mt-4 text-sm">Preparation readiness is unavailable for this checklist response. Review the requirements below.</p>;
 const next=readiness.items.find(item=>item.state!=='complete');
 const stateLabels={complete:'Reviewed preparation check complete',missing:'Missing information or evidence','needs-review':'Evidence needs review',difference:'Reviewed difference needs investigation','official-check':'Official applicability / acceptance unverified'};
 return <section aria-label="Passport preparation readiness" className="mt-5 space-y-3 rounded-xl border border-teal-200 bg-teal-50 p-4 text-[#173f68] dark:border-teal-700 dark:bg-[#173B40] dark:text-slate-100">
  <h3 className="text-lg font-bold">Preparation {readiness.percentage}% complete</h3>
  <div role="progressbar" aria-label="Preparation readiness" aria-valuemin={0} aria-valuemax={100} aria-valuenow={readiness.percentage} className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"><div style={{width:`${readiness.percentage}%`}} className="h-full bg-teal-700 dark:bg-teal-400"/></div>
  <p className="text-sm">{readiness.completed_checks} of {readiness.total_checks} applicable preparation checks complete. Wizard navigation is separate. Government acceptance remains unverified.</p>
  <p className="text-xs">{readiness.formula} Only matching, applicant-owned evidence with reviewed required fields can complete an evidence check. Unresolved reviewed differences remain pending.</p>
  <ul className="space-y-2">{readiness.items.map(item=><li key={item.id} className="rounded-lg border border-teal-200 bg-white p-3 text-sm dark:border-teal-800 dark:bg-[#162430]"><strong>{item.title}</strong><span className="block font-medium">{stateLabels[item.state]}</span><p>{item.reason}</p>{item.document_ids.length>0&&<p>Documents: {item.document_ids.map(id=>filenames.get(id)??'Unavailable saved document').join(', ')}</p>}{item.state!=='complete'&&<p className="mt-1">Next: {item.next_action}</p>}</li>)}</ul>
  <p className="text-sm font-semibold">Next action: {next?.next_action??'Verify current requirements and acceptance with Passport Seva before applying.'}</p>
  <div className="flex flex-wrap gap-3 text-sm font-semibold text-teal-800 dark:text-teal-200"><Link to="/documents" className="underline">Review evidence</Link><Link to="/planner" className="underline">Open Resolution Planner</Link><Link to="/applications" className="underline">Saved preparations and next steps</Link></div>
 </section>;
}
