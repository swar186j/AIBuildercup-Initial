import {useEffect,useState} from 'react';
import {Activity,ArrowRight,CheckCircle2,FileCheck2,FileUp,LayoutDashboard,LockKeyhole,ShieldCheck,Sparkles,X} from 'lucide-react';
import {getHealth,type Health} from './api';

type Intake={scheme:string,applicant:string,reference:string,notes:string};
export default function App(){
 const [health,setHealth]=useState<Health|null>(null);
 const [error,setError]=useState('');
 const [file,setFile]=useState<File|null>(null);
 const [intake,setIntake]=useState<Intake>({scheme:'ESIC medical evidence',applicant:'',reference:'',notes:''});
 const [showReview,setShowReview]=useState(false);
 useEffect(()=>{getHealth().then(setHealth).catch(e=>setError(String(e)))},[]);
 function update(key:keyof Intake,value:string){setIntake(v=>({...v,[key]:value}))}
 return <div className="app"><aside className="sidebar"><div className="brand"><div className="brand-icon"><ShieldCheck size={23}/></div><div><b>Draft1</b><small>EVIDENCE INTELLIGENCE</small></div></div><div className="nav"><div className="nav-active"><LayoutDashboard size={18}/> Workspace</div><div className="nav-disabled"><FileCheck2 size={18}/> Cases <span>soon</span></div><div className="nav-disabled"><Activity size={18}/> Activity <span>soon</span></div></div><div className="sidebar-bottom"><LockKeyhole size={16}/> Human-in-the-loop by design</div></aside>
 <main><header><span>Workspace <span className="slash">/</span> New evidence case</span><div className={'status '+(health?'online':'offline')}><span className="dot"/>{health?'API connected':error?'API offline':'Connecting...'}</div></header>
 <div className="content"><div className="eyebrow"><Sparkles size={15}/> AI-ASSISTED EVIDENCE WORKFLOW</div><h1>Turn evidence into<br/><em>actionable decisions.</em></h1><p className="subtitle">Collect supporting documents, prepare a structured case, and keep final decisions with a human reviewer.</p>
 <div className="steps"><div className="step current"><span>01</span> Evidence intake</div><div className="step"><span>02</span> AI validation</div><div className="step"><span>03</span> Officer review</div></div>
 <div className="columns"><section className="panel"><div className="panel-heading"><div><h2>New evidence case</h2><p>Start by adding case details and one supporting file.</p></div><FileUp size={22}/></div>
 <label>Workflow</label><select value={intake.scheme} onChange={e=>update('scheme',e.target.value)}><option>ESIC medical evidence</option><option>PMAY-G evidence reconciliation</option><option>General evidence review</option></select>
 <div className="two"><div><label>Applicant / case name</label><input placeholder="Enter a case name" value={intake.applicant} onChange={e=>update('applicant',e.target.value)}/></div><div><label>Reference ID (optional)</label><input placeholder="e.g. CASE-1001" value={intake.reference} onChange={e=>update('reference',e.target.value)}/></div></div>
 <label>Supporting document</label><label className="upload"><input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e=>setFile(e.target.files?.[0]??null)}/><FileUp size={26}/><strong>{file?file.name:'Choose a document'}</strong><span>{file?`${(file.size/1024).toFixed(1)} KB`:'PDF, JPG or PNG · Up to 10 MB'}</span></label>
 <label>Additional context (optional)</label><textarea rows={3} placeholder="Add details the reviewer should know..." value={intake.notes} onChange={e=>update('notes',e.target.value)}/>
 <button className="primary" disabled={!intake.applicant.trim()||!file||file.size>10*1024*1024} onClick={()=>setShowReview(true)}>Review case details <ArrowRight size={17}/></button><p className="hint">This is a local preview. No document is uploaded until the backend submission API is implemented.</p>
 </section><div className="right"><section className="info"><div className="info-icon"><ShieldCheck size={22}/></div><h3>Evidence you can trust</h3><p>Designed to distinguish extracted document facts, rule-based checks, and human decisions.</p><div className="feature"><CheckCircle2 size={17}/> Structured evidence intake</div><div className="feature"><CheckCircle2 size={17}/> Explainable verification pipeline</div><div className="feature"><CheckCircle2 size={17}/> Human approval before action</div></section><section className="info secondary"><h3>Development status</h3><div className="statline"><span>Backend health</span><b>{health?.status??'Unavailable'}</b></div><div className="statline"><span>API version</span><b>{health?.version??'—'}</b></div><div className="statline"><span>Submission endpoint</span><b>Not connected</b></div></section></div></div>
 <footer>Draft1 · AI Builder Cup prototype · Use synthetic documents for testing</footer></div></main>
 {showReview&&<div className="overlay" role="presentation" onMouseDown={()=>setShowReview(false)}><div className="modal" role="dialog" aria-modal="true" aria-label="Case preview" onMouseDown={e=>e.stopPropagation()}><button className="close" aria-label="Close" onClick={()=>setShowReview(false)}><X size={20}/></button><div className="eyebrow">CASE PREVIEW</div><h2>Ready for backend integration</h2><p>Your intake details are captured locally. The API to submit and analyze evidence has not been implemented yet.</p><dl><dt>Workflow</dt><dd>{intake.scheme}</dd><dt>Case</dt><dd>{intake.applicant}</dd><dt>Reference</dt><dd>{intake.reference||'—'}</dd><dt>Document</dt><dd>{file?.name}</dd><dt>Context</dt><dd>{intake.notes||'—'}</dd></dl><button className="primary" onClick={()=>setShowReview(false)}>Back to intake</button></div></div>}
 </div>
}
