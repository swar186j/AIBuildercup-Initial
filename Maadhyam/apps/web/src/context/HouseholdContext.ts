import { createContext, useContext } from "react";
export type Relation='self'|'parent'|'guardian'|'spouse'|'child'|'sibling'|'other';
export type HouseholdMember={createdAt?:string;updatedAt?:string;id:string;label:string;relationship:Relation;dependsOnMemberIds:string[];dependsOnDocumentIds:string[];relationshipEvidenceDocumentIds:string[]};
export type Value={members:HouseholdMember[];memberEditRevision:number;addMember:(label:string,relationship:Relation)=>void;editMember:(id:string,patch:Partial<HouseholdMember>)=>void;removeMember:(id:string)=>void;associate:(documentId:string,memberId:string,confirmed:boolean)=>boolean;unassign:(documentId:string)=>void;restoreMembers:(items:HouseholdMember[])=>void};
export const Context=createContext<Value|null>(null);
export function useHousehold(){const value=useContext(Context);if(!value)throw new Error('Household workspace unavailable');return value;}
