import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useDocuments, type DocumentHolder } from './DocumentContext';
export type Relation='self'|'parent'|'guardian'|'spouse'|'child'|'sibling'|'other';
export type HouseholdMember={id:string;label:string;relationship:Relation;dependsOnMemberIds:string[];dependsOnDocumentIds:string[];relationshipEvidenceDocumentIds:string[]};
type Value={members:HouseholdMember[];addMember:(label:string,relationship:Relation)=>void;editMember:(id:string,patch:Partial<HouseholdMember>)=>void;removeMember:(id:string)=>void;associate:(documentId:string,memberId:string,confirmed:boolean)=>boolean;unassign:(documentId:string)=>void};
const Context=createContext<Value|null>(null);
export function HouseholdProvider({children}:{children:ReactNode}){
 const {documents,updateMetadata}=useDocuments();
 const [members,setMembers]=useState<HouseholdMember[]>([{id:'applicant',label:'Applicant (this workspace)',relationship:'self',dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}]);
 const docKey=documents.map(d=>d.id).sort().join('|');
 useEffect(()=>{const ids=new Set(docKey.split('|'));setMembers(old=>old.map(m=>({...m,dependsOnDocumentIds:m.dependsOnDocumentIds.filter(id=>ids.has(id)),relationshipEvidenceDocumentIds:m.relationshipEvidenceDocumentIds.filter(id=>ids.has(id))})));},[docKey]);
 function addMember(label:string,relationship:Relation){if(!label.trim()||relationship==='self'||members.length>=30)return;setMembers(old=>[...old,{id:crypto.randomUUID(),label:label.trim(),relationship,dependsOnMemberIds:[],dependsOnDocumentIds:[],relationshipEvidenceDocumentIds:[]}]);}
 function editMember(id:string,patch:Partial<HouseholdMember>){
  const member=members.find(m=>m.id===id);if(!member)return;
  const relationship=id==='applicant'?'self':patch.relationship??member.relationship;
  if(relationship==='self'&&id!=='applicant')return;
  setMembers(old=>old.map(m=>m.id===id?{...m,...patch,id,relationship}:m));
  if(patch.relationship)documents.filter(d=>d.metadata.householdMemberId===id).forEach(d=>updateMetadata(d.id,{...d.metadata,holder:holder(relationship)}));
 }
 function holder(relation:Relation):DocumentHolder{return relation==='self'?'self':relation==='parent'||relation==='guardian'?'parent-guardian':relation==='spouse'?'spouse':'other';}
 function unassign(documentId:string){setMembers(old=>old.map(m=>({...m,dependsOnDocumentIds:m.dependsOnDocumentIds.filter(id=>id!==documentId),relationshipEvidenceDocumentIds:m.relationshipEvidenceDocumentIds.filter(id=>id!==documentId)})));const d=documents.find(d=>d.id===documentId);if(d)updateMetadata(d.id,{...d.metadata,holder:'other',householdMemberId:undefined,associationConsent:undefined});}
 function removeMember(id:string){if(id==='applicant')return;documents.filter(d=>d.metadata.householdMemberId===id).forEach(d=>unassign(d.id));setMembers(old=>old.filter(m=>m.id!==id).map(m=>({...m,dependsOnMemberIds:m.dependsOnMemberIds.filter(x=>x!==id)})));}
 function associate(documentId:string,memberId:string,confirmed:boolean){const m=members.find(m=>m.id===memberId);const d=documents.find(d=>d.id===documentId);if(!m||!d||!confirmed)return false;updateMetadata(d.id,{...d.metadata,holder:holder(m.relationship),householdMemberId:memberId,associationConsent:true});return true;}
 return <Context.Provider value={{members,addMember,editMember,removeMember,associate,unassign}}>{children}</Context.Provider>;
}
export function useHousehold(){const value=useContext(Context);if(!value)throw new Error('Household workspace unavailable');return value;}
