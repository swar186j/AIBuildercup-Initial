import {trackCloudSave} from './saveNotifications';
import { ensureDemoUser } from './firebaseClient';
import type { DocumentMetadata, LocalDocument, ReviewStatus } from '../context/DocumentContext';
const base=(import.meta.env.VITE_API_BASE_URL as string|undefined)?.replace(/\/+$/,'') || (import.meta.env.DEV?'http://127.0.0.1:8000':'');
export type CloudDocument={id:string;filename:string;contentType:string;sizeBytes:number;metadata:DocumentMetadata;status:ReviewStatus;revision:number;storageStatus:'pending'|'ready'|'deleting';createdAt:string;uploadedAt?:string;updatedAt?:string;originalLocalAddedAt?:string;sha256:string};
function validDocument(value:unknown):value is CloudDocument {
 if(!value||typeof value!=='object')return false;
 const d=value as CloudDocument;
 return typeof d.id==='string'&&typeof d.filename==='string'&&typeof d.contentType==='string'&&Number.isFinite(d.sizeBytes)&&Number.isInteger(d.revision)&&!!d.metadata&&typeof d.metadata==='object'&&['self','parent-guardian','spouse','other'].includes(d.metadata.holder)&&['identity','address','birth','education','employment','other'].includes(d.metadata.category)&&typeof d.metadata.documentType==='string'&&['reviewed','needs-review'].includes(d.status)&&['pending','ready','deleting'].includes(d.storageStatus)&&[d.metadata.printedName,d.metadata.dateOfBirth,d.metadata.residentialAddress].every(v=>v==null||typeof v==='string');
}
async function performRequest(path:string,init:RequestInit={},expectedUid?:string) {
 const user=await ensureDemoUser();
 if(expectedUid&&user.uid!==expectedUid)throw new Error('Account changed. Operation canceled.');
 const token=await user.getIdToken();
 const response=await fetch(`${base}/api/documents${path}`,{...init,headers:{Authorization:`Bearer ${token}`,...init.headers},cache:'no-store',signal:AbortSignal.timeout(40000)});
 if(!response.ok){const data=await response.json().catch(()=>null);throw new Error(response.status===409?'Cloud revision conflict — edits retained. Reload and compare before retrying.':data?.error?.message||`Cloud Vault request failed (${response.status}).`);}
 return response;
}
async function request(path:string,init:RequestInit={},uid?:string):Promise<Response>{
 if(!init.method||init.method==='GET')return performRequest(path,init,uid);
 const label=init.method==='POST'?'Document saved to cloud':init.method==='PATCH'?'Changes saved': 'Document deleted';
 return trackCloudSave(`document:${path}`,label,async()=>{
   const response=await performRequest(path,init,uid);
   if(init.method!=='DELETE'){
     const result:unknown=await response.clone().json();
     if(!result||typeof result!=='object')throw new Error('Invalid document save acknowledgment.');
     const record=result as CloudDocument;
     if(!validDocument(record)||typeof record.updatedAt!=='string'||record.storageStatus!=='ready')throw new Error('Document persistence was not confirmed. Retry from Document Vault.');
     if(init.method==='POST'&&init.body instanceof FormData&&record.id!==init.body.get('document_id'))throw new Error('Wrong document in upload acknowledgment.');
     if(init.method==='PATCH'){
       const sent=JSON.parse(String(init.body)) as {revision:number};
       if(record.id!==decodeURIComponent(path.slice(1))||record.revision<=sent.revision)throw new Error('Document revision was not confirmed.');
     }
   }
   return response;
 });
}
export const cloudDocuments={
 async list(uid?:string):Promise<CloudDocument[]>{const data:unknown=await (await request('',{},uid)).json();if(!Array.isArray(data)||!data.every(validDocument))throw new Error('Invalid cloud document list; local records retained.');return data;},
 async upload(document:LocalDocument,uid?:string):Promise<CloudDocument>{
  const body=new FormData();body.set('document_id',document.id);body.set('cloud_storage_consent','true');body.set('fields',JSON.stringify({metadata:document.metadata,status:document.status,originalLocalAddedAt:document.addedAt.toISOString()}));
  const type=document.file.type || ({pdf:'application/pdf',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg'}[document.file.name.split('.').pop()?.toLowerCase()||'']||'');
  body.set('file',new File([document.file],document.file.name,{type}));
  return (await request('',{method:'POST',body},uid)).json();
 },
 async file(id:string,uid?:string):Promise<Blob>{return (await request(`/${encodeURIComponent(id)}/file`,{},uid)).blob();},
 async patch(id:string,revision:number,metadata:DocumentMetadata,status:ReviewStatus,uid?:string):Promise<CloudDocument>{return (await request(`/${encodeURIComponent(id)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision,metadata:{...metadata,householdMemberId:metadata.householdMemberId??null,associationConsent:metadata.associationConsent??false},status})},uid)).json();},
 async remove(id:string,revision:number,uid?:string){await request(`/${encodeURIComponent(id)}?revision=${revision}`,{method:'DELETE'},uid);},
 async clear(uid?:string):Promise<{deleted:string[];failed:string[]}>{return trackCloudSave('vault-delete','Documents deleted',async()=>{const data:unknown=await (await performRequest('',{method:'DELETE'},uid)).json();if(!data||typeof data!=='object'||!('deleted' in data)||!Array.isArray(data.deleted)||!('failed' in data)||!Array.isArray(data.failed))throw new Error('Invalid deletion acknowledgment');return data as {deleted:string[];failed:string[]};},result=>result.failed.length>0);},
};
