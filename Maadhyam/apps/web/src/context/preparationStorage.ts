import { initialPassportAnswers, type PassportAssistanceType, type PassportJourneyAnswers } from '../data/journeyData';
export type JourneyData = { schemaVersion:1; service:'passport'; assistanceType:PassportAssistanceType; answers:PassportJourneyAnswers; stepIndex:number; applicantDob:string; applicantName:string; documentIds:string[] };
export function newJourney(type:PassportAssistanceType='fresh'):JourneyData { return {schemaVersion:1,service:'passport',assistanceType:type,answers:{...initialPassportAnswers,assistanceType:type},stepIndex:0,applicantDob:'',applicantName:'',documentIds:[]}; }
export function validDate(value:string) { return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0,10)===value; }
export function readJourney(value:unknown):JourneyData|null {
 if(!value||typeof value!=='object')return null;
 const v=value as Record<string,unknown>;
 if(v.schemaVersion!==1||v.service!=='passport'||!['fresh','reissue','correction','documents','police'].includes(String(v.assistanceType))||!Number.isInteger(v.stepIndex)||Number(v.stepIndex)<0||Number(v.stepIndex)>3||typeof v.applicantDob!=='string'||(v.applicantDob!==''&&!validDate(v.applicantDob))||typeof v.applicantName!=='string'||v.applicantName.length>200||!v.answers||typeof v.answers!=='object')return null;
 const ids=v.documentIds??[];
 if(!Array.isArray(ids)||ids.length>60||!ids.every(id=>typeof id==='string'&&id.length>0&&id.length<=128)||new Set(ids).size!==ids.length)return null;
 const a=v.answers as Record<string,unknown>;
 const allowed:Record<string,string[]>={assistanceType:[String(v.assistanceType)],applicantAgeGroup:['','adult','minor'],currentAddressMatches:['','yes','no','unsure'],hasIdentityDocument:['','yes','no','unsure'],hasAddressDocument:['','yes','no','unsure'],hasDateOfBirthDocument:['','yes','no','unsure'],nameConsistent:['','yes','no','unsure'],policeVerificationStatus:['','not-started','pending','completed','delayed','adverse','unknown']};
 if(!Object.entries(allowed).every(([key,options])=>typeof a[key]==='string'&&options.includes(a[key] as string)))return null;
 return {schemaVersion:1,service:'passport',assistanceType:v.assistanceType as PassportAssistanceType,documentIds:ids,stepIndex:Number(v.stepIndex),applicantDob:v.applicantDob,applicantName:v.applicantName,answers:Object.fromEntries(Object.keys(allowed).map(k=>[k,a[k]])) as unknown as PassportJourneyAnswers};
}
