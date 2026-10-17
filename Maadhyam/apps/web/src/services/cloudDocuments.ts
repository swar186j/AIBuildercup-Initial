import { ensureDemoUser } from './firebaseClient';
import type { DocumentMetadata, LocalDocument, ReviewStatus } from '../context/DocumentContext';
const base=(import.meta.env.VITE_API_BASE_URL as string|undefined)?.replace(/\/+$/,'') || (import.meta.env.DEV?'http://127.0.0.1:8000':'');
export type CloudDocument={id:string;filename:string;contentType:string;sizeBytes:number;metadata:DocumentMetadata;status:ReviewStatus;revision:number;storageStatus:'pending'|'ready'|'deleting';createdAt:string;uploadedAt?:string;updatedAt?:string;originalLocalAddedAt?:string;sha256:string};
async function request(path:string,init:RequestInit={},expectedUid?:string) {
 const user=await ensureDemoUser();
 if(expectedUid&&user.uid!==expectedUid)throw new Error('Account changed. Operation canceled.');
 const token=await user.getIdToken();
 const response=await fetch(`${base}/api/documents${path}`,{...init,headers:{Authorization:`Bearer ${token}`,...init.headers},cache:'no-store',signal:AbortSignal.timeout(40000)});
 if(!response.ok){const data=await response.json().catch(()=>null);throw new Error(response.status===409?'Cloud revision conflict — edits retained. Reload and compare before retrying.':data?.error?.message||`Cloud Vault request failed (${response.status}).`);}
 return response;
}
export const cloudDocuments={
 async list(uid?:string):Promise<CloudDocument[]>{return (await request('',{},uid)).json();},
 async upload(document:LocalDocument,uid?:string):Promise<CloudDocument>{
  const body=new FormData();body.set('document_id',document.id);body.set('cloud_storage_consent','true');body.set('fields',JSON.stringify({metadata:document.metadata,status:document.status,originalLocalAddedAt:document.addedAt.toISOString()}));
  const type=document.file.type || ({pdf:'application/pdf',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg'}[document.file.name.split('.').pop()?.toLowerCase()||'']||'');
  body.set('file',new File([document.file],document.file.name,{type}));
  return (await request('',{method:'POST',body},uid)).json();
 },
 async file(id:string,uid?:string):Promise<Blob>{return (await request(`/${encodeURIComponent(id)}/file`,{},uid)).blob();},
 async patch(id:string,revision:number,metadata:DocumentMetadata,status:ReviewStatus,uid?:string):Promise<CloudDocument>{return (await request(`/${encodeURIComponent(id)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision,metadata,status})},uid)).json();},
 async remove(id:string,revision:number,uid?:string){await request(`/${encodeURIComponent(id)}?revision=${revision}`,{method:'DELETE'},uid);},
 async clear(uid?:string):Promise<{deleted:string[];failed:string[]}>{return (await request('',{method:'DELETE'},uid)).json();},
};
