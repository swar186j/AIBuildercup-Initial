import { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
export default function PreparationStorageControls(){
 const {preparationSaving,setPreparationSaving,storageNotice}=useWorkspace();const [consent,setConsent]=useState(false);
 return <section aria-label="Preparation storage controls" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-100">
 <h2 className="font-bold">Preparation saving</h2><p className="mt-1">Off by default. Session records survive navigation, but disappear on reload. Browser-local saving keeps applicant answers, DOB and progress on this device. It is not encrypted; use fictional data and avoid shared devices. Vault file saving is controlled separately.</p>
 {!preparationSaving&&<label className="mt-3 flex gap-2"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>I understand and consent to saving preparation details in this browser.</label>}
 <button type="button" disabled={!preparationSaving&&!consent} onClick={()=>{setPreparationSaving(!preparationSaving);setConsent(false);}} className="mt-3 rounded-lg border border-teal-700 px-4 py-2 font-semibold text-teal-700 disabled:opacity-40">{preparationSaving?'Disable preparation saving and delete local copies':'Enable preparation saving'}</button>
 {storageNotice&&<p role="status" className="mt-2">{storageNotice}</p>}
 </section>;
}
