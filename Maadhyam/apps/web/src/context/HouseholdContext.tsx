/* eslint react-refresh/only-export-components: ["error", { "allowExportNames": ["useHousehold"] }] */
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useDocuments, type DocumentHolder } from './DocumentContext';
import { useAuth } from './AuthContext';
import { loadHousehold, saveHousehold } from '../services/cloudWorkspace';
export type Relation='self'|'parent'|'guardian'|'spouse'|'child'|'sibling'|'other';
export type HouseholdMember={id:string;label:string;relationship:Relation;dependsOnMemberIds:string[];dependsOnDocumentIds:string[];relationshipEvidenceDocumentIds:string[]};
type Value={ready:boolean;cloudBusy:boolean;cloudError:string;storageNotice:string;retryCloud:()=>void;members:HouseholdMember[];addMember:(label:string,relationship:Relation)=>void;editMember:(id:string,patch:Partial<HouseholdMember>)=>void;removeMember:(id:string)=>void;associate:(documentId:string,memberId:string,confirmed:boolean)=>boolean;unassign:(documentId:string)=>void};
const Context=createContext<Value|null>(null);
export function HouseholdProvider({children}:{children:ReactNode}){
 const {documents,updateMetadata,persistenceReady}=useDocuments();
 const {registerLogoutGuard}=useAuth();
 const [members,setMembers]=useState<HouseholdMember[]>([{id:'applicant',label:'Applicant (this workspace)',relationship:'self',dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}]);

 const [ready,setReady]=useState(false);
 const [pending,setPending]=useState(0);
 const [cloudError,setCloudError]=useState('');
 const [storageNotice,setStorageNotice]=useState('Loading your saved household…');
 const [attempt,setAttempt]=useState(0);
 const revision=useRef(0);
 const confirmed=useRef('');
 const queue=useRef(Promise.resolve());
 const active=useRef(0);
 const latest=useRef(members);
 useEffect(()=>{latest.current=members;},[members]);
 useEffect(()=>{
  const generation=++active.current;
  void loadHousehold().then(result=>{
   if(generation!==active.current)return;
   revision.current=result.revision;
   const restored=result.members.length?result.members:[{id:'applicant',label:'Applicant (this workspace)',relationship:'self' as const,dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}];
   confirmed.current=JSON.stringify(restored);
   setMembers(restored);setReady(true);setCloudError('');setStorageNotice('Household saved to your account.');
  }).catch(error=>{if(generation===active.current)setCloudError(error instanceof Error?error.message:'Household could not load.');});
  return()=>{active.current+=1;};
 },[attempt]);
 useEffect(()=>{
  if(!ready||JSON.stringify(members)===confirmed.current)return;
  const generation=active.current;
  const snapshot=members;
  queueMicrotask(()=>setPending(count=>count+1));
  queue.current=queue.current.catch(()=>{}).then(async()=>{
   if(generation!==active.current)return;
   const result=await saveHousehold(snapshot,revision.current);
   if(generation!==active.current)return;
   revision.current=result.revision;confirmed.current=JSON.stringify(snapshot);
   setCloudError('');setStorageNotice('Household changes saved.');
  }).catch(error=>{if(generation===active.current)setCloudError(error instanceof Error?error.message:'Household save failed.');})
   .finally(()=>{if(generation===active.current)setPending(count=>Math.max(0,count-1));});
 },[members,ready]);
 const dirty=ready&&JSON.stringify(members)!==confirmed.current;
 useEffect(()=>registerLogoutGuard(()=>pending===0&&!dirty),[registerLogoutGuard,pending,dirty]);
 useEffect(()=>{
  if(!pending&&!dirty)return;
  const warn=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue='';};
  window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn);
 },[pending,dirty]);
 function retryCloud(){
  if(!ready){setAttempt(value=>value+1);return;}
  setMembers([...latest.current]);
 }
 const docKey=documents.map(d=>d.id).sort().join('|');
 useEffect(()=>{if(!ready||!persistenceReady)return;let active=true;queueMicrotask(()=>{if(!active)return;const ids=new Set(docKey.split('|'));setMembers(old=>old.map(m=>({...m,dependsOnDocumentIds:m.dependsOnDocumentIds.filter(id=>ids.has(id)),relationshipEvidenceDocumentIds:m.relationshipEvidenceDocumentIds.filter(id=>ids.has(id))})));});return()=>{active=false;};},[docKey,ready,persistenceReady]);
 function addMember(label:string,relationship:Relation){if(!ready||pending)return;if(!label.trim()||relationship==='self'||members.length>=30)return;setMembers(old=>[...old,{id:crypto.randomUUID(),label:label.trim(),relationship,dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}]);}
 function editMember(id:string,patch:Partial<HouseholdMember>){
  if(!ready)return;
  const member=members.find(m=>m.id===id);if(!member)return;
  const relationship=id==='applicant'?'self':patch.relationship??member.relationship;
  if(relationship==='self'&&id!=='applicant')return;
  setMembers(old=>old.map(m=>m.id===id?{...m,...patch,id,relationship}:m));
  if(patch.relationship)documents.filter(d=>d.metadata.householdMemberId===id).forEach(d=>updateMetadata(d.id,{...d.metadata,holder:holder(relationship)}));
 }
 function holder(relation:Relation):DocumentHolder{return relation==='self'?'self':relation==='parent'||relation==='guardian'?'parent-guardian':relation==='spouse'?'spouse':'other';}
 function unassign(documentId:string){if(!ready)return;setMembers(old=>old.map(m=>({...m,dependsOnDocumentIds:m.dependsOnDocumentIds.filter(id=>id!==documentId),relationshipEvidenceDocumentIds:m.relationshipEvidenceDocumentIds.filter(id=>id!==documentId)})));const d=documents.find(d=>d.id===documentId);if(d)updateMetadata(d.id,{...d.metadata,holder:'other',householdMemberId:undefined,associationConsent:undefined});}
 function removeMember(id:string){if(!ready)return;if(id==='applicant')return;documents.filter(d=>d.metadata.householdMemberId===id).forEach(d=>unassign(d.id));setMembers(old=>old.filter(m=>m.id!==id).map(m=>({...m,dependsOnMemberIds:m.dependsOnMemberIds.filter(x=>x!==id)})));}
 function associate(documentId:string,memberId:string,confirmed:boolean){if(!ready)return false;const m=members.find(m=>m.id===memberId);const d=documents.find(d=>d.id===documentId);if(!m||!d||!confirmed)return false;updateMetadata(d.id,{...d.metadata,holder:holder(m.relationship),householdMemberId:memberId,associationConsent:true});return true;}
 return <Context.Provider value={{ready,cloudBusy:pending>0,cloudError,storageNotice,retryCloud,members,addMember,editMember,removeMember,associate,unassign}}>{children}</Context.Provider>;
}
export function useHousehold(){const value=useContext(Context);if(!value)throw new Error('Household workspace unavailable');return value;}
