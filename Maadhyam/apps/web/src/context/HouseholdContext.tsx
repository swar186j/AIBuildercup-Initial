import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { useDocuments, type DocumentHolder } from './DocumentContext';
export type Relation='self'|'parent'|'guardian'|'spouse'|'child'|'sibling'|'other';
export type HouseholdMember={id:string;label:string;relationship:Relation;dependsOnMemberIds:string[];dependsOnDocumentIds:string[];relationshipEvidenceDocumentIds:string[]};
type Value={members:HouseholdMember[];addMember:(label:string,relationship:Relation)=>void;editMember:(id:string,patch:Partial<HouseholdMember>)=>void;removeMember:(id:string)=>void;associate:(documentId:string,memberId:string,confirmed:boolean)=>boolean;unassign:(documentId:string)=>void;restoreMembers:(items:HouseholdMember[])=>void};
const Context=createContext<Value|null>(null);
export function HouseholdProvider({children}:{children:ReactNode}){
 const {documents,updateMetadata}=useDocuments();
 const [members,setMembers]=useState<HouseholdMember[]>([{id:'applicant',label:'Applicant (this workspace)',relationship:'self',dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}]);
 const docKey=documents.map(d=>d.id).sort().join('|');
 const observedDocs=useRef(new Set(documents.map(d=>d.id)));
 useEffect(()=>{
  const currentIds=new Set(documents.map(d=>d.id));
  const deleted=[...observedDocs.current].filter(id=>!currentIds.has(id));
  observedDocs.current=currentIds;
  // Remove only documents actually deleted in this browser, NOT cloud references
  // whose file bytes were never available on this device.
  if(deleted.length){const removed=new Set(deleted);setMembers(old=>old.map(m=>({...m,dependsOnDocumentIds:m.dependsOnDocumentIds.filter(id=>!removed.has(id)),relationshipEvidenceDocumentIds:m.relationshipEvidenceDocumentIds.filter(id=>!removed.has(id))})));}
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[docKey]);
 function addMember(label:string,relationship:Relation){if(!label.trim()||relationship==='self'||members.length>=30)return;setMembers(old=>[...old,{id:crypto.randomUUID(),label:label.trim(),relationship,dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}]);}
 function editMember(id:string,patch:Partial<HouseholdMember>){
  const member=members.find(m=>m.id===id);if(!member)return;
  const relationship=id==='applicant'?'self':patch.relationship??member.relationship;
  if(relationship==='self'&&id!=='applicant')return;
  const safePatch=patch.dependsOnMemberIds
    ? {...patch,dependsOnMemberIds:patch.dependsOnMemberIds.filter(dep=>dep!==id)}
    : patch;
  setMembers(old=>old.map(m=>m.id===id?{...m,...safePatch,id,relationship}:m));
  if(patch.relationship)documents.filter(d=>d.metadata.householdMemberId===id).forEach(d=>updateMetadata(d.id,{...d.metadata,holder:holder(relationship)}));
 }
 function restoreMembers(items:HouseholdMember[]) {
  if (!Array.isArray(items) || items.length > 30) return;
  if (items.length === 0) {
    setMembers([{
      id:'applicant',
      label:'Applicant (this workspace)',
      relationship:'self',
      dependsOnMemberIds:[],
      dependsOnDocumentIds:[],
      relationshipEvidenceDocumentIds:[],
    }]);
    return;
  }
  const relations:Relation[]=['self','parent','guardian','spouse','child','sibling','other'];
  const ids = new Set<string>();
  for (const m of items) {
    if (!m || typeof m.id !== 'string' || !m.id || m.id.length > 128 || ids.has(m.id) ||
      typeof m.label !== 'string' || !m.label.trim() || m.label.length > 200 ||
      !relations.includes(m.relationship) || (m.id === 'applicant') !== (m.relationship === 'self') ||
      ![m.dependsOnMemberIds,m.dependsOnDocumentIds,m.relationshipEvidenceDocumentIds].every(
        list=>Array.isArray(list) && list.length<=60 && list.every(id=>typeof id==='string'&&id.length<=128)
      )) return;
    ids.add(m.id);
  }
  if (!ids.has('applicant')) return;
  setMembers(items.map(m=>({
    ...m,
    dependsOnMemberIds:m.dependsOnMemberIds.filter(dep=>ids.has(dep)&&dep!==m.id),
    // Retain absent reference IDs; they are NOT proof of accessible Vault files.
    dependsOnDocumentIds:[...m.dependsOnDocumentIds],
    relationshipEvidenceDocumentIds:[...m.relationshipEvidenceDocumentIds],
  })));
 }
 function holder(relation:Relation):DocumentHolder{return relation==='self'?'self':relation==='parent'||relation==='guardian'?'parent-guardian':relation==='spouse'?'spouse':'other';}
 function unassign(documentId:string){setMembers(old=>old.map(m=>({...m,dependsOnDocumentIds:m.dependsOnDocumentIds.filter(id=>id!==documentId),relationshipEvidenceDocumentIds:m.relationshipEvidenceDocumentIds.filter(id=>id!==documentId)})));const d=documents.find(d=>d.id===documentId);if(d)updateMetadata(d.id,{...d.metadata,holder:'other',householdMemberId:undefined,associationConsent:undefined});}
 function removeMember(id:string){if(id==='applicant')return;documents.filter(d=>d.metadata.householdMemberId===id).forEach(d=>unassign(d.id));setMembers(old=>old.filter(m=>m.id!==id).map(m=>({...m,dependsOnMemberIds:m.dependsOnMemberIds.filter(x=>x!==id)})));}
 function associate(documentId:string,memberId:string,confirmed:boolean){const m=members.find(m=>m.id===memberId);const d=documents.find(d=>d.id===documentId);if(!m||!d||!confirmed)return false;updateMetadata(d.id,{...d.metadata,holder:holder(m.relationship),householdMemberId:memberId,associationConsent:true});return true;}
 return <Context.Provider value={{members,addMember,editMember,removeMember,associate,unassign,restoreMembers}}>{children}</Context.Provider>;
}
export function useHousehold(){const value=useContext(Context);if(!value)throw new Error('Household workspace unavailable');return value;}
