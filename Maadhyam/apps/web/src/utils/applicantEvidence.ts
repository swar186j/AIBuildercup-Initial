import type {LocalDocument} from '../context/DocumentContext';
import {comparisonOwner} from './documentComparison';

/** Citizen-confirmed ownership, not legal identity verification. Legacy self is
 * the single workspace applicant; generic family categories never identify one. */
export function applicantEvidence(documents:LocalDocument[],memberId:string|undefined,knownIds:ReadonlySet<string>):LocalDocument[]{
 const owner=`member:${memberId||'applicant'}`;
 return documents.filter(d=>comparisonOwner(d,knownIds)===owner);
}

/** Adapt a selected household person to the existing applicant reasoning API.
 * Clones only: stable IDs and real Vault metadata are never changed. */
export function asApplicantEvidence(documents:LocalDocument[]):LocalDocument[]{
 return documents.map(d=>({...d,metadata:{...d.metadata,holder:'self',householdMemberId:undefined,associationConsent:undefined}}));
}
