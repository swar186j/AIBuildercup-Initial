import {trackCloudSave} from '../services/saveNotifications';
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { ensureDemoUser, subscribeFirebaseUser } from '../services/firebaseClient';
import { cloudDocuments, type CloudDocument } from '../services/cloudDocuments';
import { DocumentContext, type LocalDocument, type DocumentMetadata } from "./DocumentContext";

// Browser-local IndexedDB; never transmitted to a server by this persistence layer.
// Opt-in only. Use fictional data for demos; IndexedDB is NOT encrypted at rest.
const DB_NAME = "maadhyam-local-vault-v1";
const STORE = "documents";
const PREF = "maadhyam-vault-persist-opt-in";
type StoredDocument = Omit<LocalDocument, "url" | "addedAt"> & { addedAt: number };
function openVaultDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => { if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE, { keyPath: "id" }); };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function readVault(): Promise<StoredDocument[]> {
  const db = await openVaultDB();
  try {
    return await new Promise((resolve, reject) => {
      const req = db.transaction(STORE, "readonly").objectStore(STORE).getAll();
      req.onsuccess = () => resolve(req.result as StoredDocument[]);
      req.onerror = () => reject(req.error);
    });
  } finally { db.close(); }
}
async function saveVault(docs: LocalDocument[]): Promise<void> {
  const db = await openVaultDB();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      const store = tx.objectStore(STORE);
      // Preserve other accounts and legacy originals; removal is explicit.
      docs.filter(d=>!d.cloud || d.url).forEach(({ id, file, status, metadata, addedAt,ownerUid,cloud,createdAt,uploadedAt,updatedAt,originalLocalAddedAt }) => store.put({ id, file, status, metadata, addedAt: addedAt.getTime(),ownerUid,cloud,createdAt,uploadedAt,updatedAt,originalLocalAddedAt }));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally { db.close(); }
}
async function deleteVaultIds(ids:string[]):Promise<void>{
  const db=await openVaultDB();
  try{await new Promise<void>((resolve,reject)=>{
    const tx=db.transaction(STORE,'readwrite');
    ids.forEach(id=>tx.objectStore(STORE).delete(id));
    tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);
  });}finally{db.close();}
}
async function deleteVault(): Promise<void> {
  const db = await openVaultDB();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally { db.close(); }
}

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<LocalDocument[]>([]);
  const documentsRef = useRef<LocalDocument[]>([]);
  const [storagePreference] = useState(() => {
    try { return {enabled:localStorage.getItem(PREF)==='yes', error:''}; }
    catch { return {enabled:false,error:'Browser storage is unavailable. Vault remains in this session.'}; }
  });
  const [persistenceEnabled, setPersistenceEnabled] = useState(storagePreference.enabled);
  const [persistenceReady, setPersistenceReady] = useState(false);
  const [persistenceError, setPersistenceError] = useState(storagePreference.error);
  const persistQueue = useRef<Promise<void>>(Promise.resolve());
  const persistenceEnabledRef = useRef(persistenceEnabled);
  useLayoutEffect(() => { persistenceEnabledRef.current = persistenceEnabled; }, [persistenceEnabled]);
  const hydrated = useRef(false);
  const account=useRef<string|null>(null);
  const epoch=useRef(0);
  const acknowledgedRevisions=useRef(new Map<string,number>());
  const operationQueue=useRef<Promise<void>>(Promise.resolve());
  const pendingOperations=useRef(0);
  const deletedIds=useRef(new Set<string>());
  const cacheEpoch=useRef(0);
  const [cloudBusy,setCloudBusy]=useState(false);
  const [cloudNotice,setCloudNotice]=useState('');
  const [cloudEnabled,setCloudEnabled]=useState(false);
  function cloudPreference(uid:string){try{return localStorage.getItem(`maadhyam-vault-cloud-${uid}`)==='yes';}catch{return false;}}
  function restored(record:CloudDocument,uid:string):LocalDocument {
    return {id:record.id,file:new File([],record.filename,{type:record.contentType}),url:'',status:record.status,metadata:record.metadata,addedAt:new Date(record.createdAt),ownerUid:uid,createdAt:record.createdAt,uploadedAt:record.uploadedAt,updatedAt:record.updatedAt,originalLocalAddedAt:record.originalLocalAddedAt,cloud:{revision:record.revision,sizeBytes:record.sizeBytes,state:record.storageStatus,sha256:record.sha256}};
  }
  useEffect(()=>{
    let cancelled=false;
    let unsubscribe=()=>{};
    async function connect(){
      try{
        await ensureDemoUser();
        if(cancelled)return;
        unsubscribe=subscribeFirebaseUser(user=>{
          const uid=user?.uid??null;
          if(uid===account.current)return;
          const previous=account.current;
          account.current=uid;
          const generation=++epoch.current;
          setCloudEnabled(uid?cloudPreference(uid):false);
          // Never display a previous account's cloud file or bound local cache.
          setDocuments(docs=>{docs.filter(d=>d.ownerUid&&d.ownerUid!==uid).forEach(d=>URL.revokeObjectURL(d.url));const filtered=docs.filter(d=>!d.ownerUid||d.ownerUid===uid);return filtered.length===docs.length?docs:filtered;});
          if(previous)setCloudNotice('Account changed. Previous account documents are hidden.');
          if(!uid)return;
          void Promise.all([cloudDocuments.list(uid).then(records=>({records,available:true})).catch(()=>({records:[] as CloudDocument[],available:false})), persistenceEnabledRef.current ? readVault().catch(()=>[]) : Promise.resolve([])]).then(([cloudResult,cached])=>{
            const {records,available}=cloudResult;
            if(cancelled||generation!==epoch.current||account.current!==uid)return;
            setDocuments(docs=>{
              const merged=new Map(docs.filter(d=>!d.ownerUid||d.ownerUid===uid).map(d=>[d.id,d]));
              for(const item of cached){
                if(item.ownerUid===uid && item.file instanceof File && (!available||!item.cloud||records.some(r=>r.id===item.id)) && !merged.has(item.id))merged.set(item.id,{...item,addedAt:new Date(item.addedAt),url:URL.createObjectURL(item.file)});
              }
              for(const record of records){
                const local=merged.get(record.id);
                if(!local)merged.set(record.id,restored(record,uid));
                else if(local.cloud&&local.cloud.state!=='save-failed')merged.set(record.id,{...restored(record,uid),file:local.file,url:local.url});
                // Local originals (including failed edits) are retained for explicit reconciliation.
              }
              const values=[...merged.values()];
              return values.length===docs.length&&values.every((d,i)=>d===docs[i])?docs:values;
            });
            setCloudNotice(available?`Cloud Vault restored (${records.length}). Files download when previewed.`:'Cloud Vault unavailable — local originals are retained.');
          }).catch(()=>{if(!cancelled&&generation===epoch.current)setCloudNotice('Cloud Vault unavailable — local originals are retained.');});
        });
      }catch{if(!cancelled)setCloudNotice('Cloud authentication unavailable. Local-only Vault remains available.');}
    }
    void connect();
    return()=>{cancelled=true;unsubscribe();};
  },[]);
  function enqueue(action:()=>Promise<void>):Promise<void>{
    ++epoch.current;
    pendingOperations.current++;setCloudBusy(true);
    const queued=operationQueue.current.catch(()=>{}).then(action);
    operationQueue.current=queued;
    return queued.catch(error=>{setCloudNotice(error instanceof Error?error.message:'Cloud operation failed; originals retained.');}).finally(()=>{pendingOperations.current--;setCloudBusy(pendingOperations.current>0);});
  }
  useEffect(()=>{
    if(!cloudBusy&&!documents.some(d=>d.cloud?.state==='save-failed'))return;
    const warn=(event:BeforeUnloadEvent)=>event.preventDefault();
    window.addEventListener('beforeunload',warn);
    return()=>window.removeEventListener('beforeunload',warn);
  },[cloudBusy,documents]);
  function replaceDocument(value:LocalDocument){if(value.ownerUid&&account.current!==value.ownerUid)return;setDocuments(old=>old.map(d=>d.id===value.id&&(!d.ownerUid||d.ownerUid===value.ownerUid)?value:d));}
  async function enableCloudStorage(){
    const user=await ensureDemoUser().catch(()=>null);
    if(!user){setCloudNotice('Cloud authentication failed. No files uploaded.');return;}
    if(!window.confirm('Store NEW document file bytes and reviewed metadata privately in Google Cloud under this anonymous Firebase account? This does not send documents to Gemini. Existing browser files require a separate migration. Decline to keep local-only storage.'))return;
    account.current=user.uid;
    try{localStorage.setItem(`maadhyam-vault-cloud-${user.uid}`,'yes');}catch{/* Consent remains valid for this session. */}
    setCloudEnabled(true);setCloudNotice('Cloud storage enabled for new uploads. Existing local files require explicit migration.');
  }
  async function uploadOne(document:LocalDocument,uid:string){
    if(account.current!==uid)throw new Error('Account changed; no file uploaded.');
    setCloudNotice(`Uploading ${document.file.name}…`);
    const record=await cloudDocuments.upload(document,uid);
    if(account.current!==uid)return;
    if(record.storageStatus!=='ready')throw new Error('Cloud upload incomplete. Original retained; retry.');
    const latest=documentsRef.current.find(d=>d.id===document.id);
    if(!latest&&deletedIds.current.has(document.id)){await cloudDocuments.remove(record.id,record.revision,uid);return;}
    const changed=!!latest&&(latest.metadata!==document.metadata||latest.status!==document.status);
    replaceDocument({...latest??document,ownerUid:uid,createdAt:record.createdAt,uploadedAt:record.uploadedAt,updatedAt:record.updatedAt,originalLocalAddedAt:record.originalLocalAddedAt,cloud:{revision:record.revision,sizeBytes:record.sizeBytes,state:changed?'save-failed':'ready',sha256:record.sha256}});
    setCloudNotice(changed?'Upload confirmed. Newer metadata edits remain unsaved — Retry cloud save.':'Saved to cloud. Review the document or continue Passport preparation.');
  }
  async function migrateLocalDocuments(){
    if(!window.confirm('Upload existing local file bytes and reviewed metadata to this anonymous account in Google Cloud? IDs and household associations are retained. Local originals remain until you explicitly clear them. Decline to keep them local-only.'))return;
    const uid=account.current;
    if(!uid){setCloudNotice('Wait for authentication before migration.');return;}
    const originals=documentsRef.current.filter(d=>!d.cloud&&(!d.ownerUid||d.ownerUid===uid));
    await enqueue(async()=>{await trackCloudSave('migration','Documents migrated',async()=>{
      let succeeded=0,failed=0;
      for(const doc of originals){
        try{
          await uploadOne(doc,uid);
          const blob=await cloudDocuments.file(doc.id,uid);
          const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))).map(x=>x.toString(16).padStart(2,'0')).join('');
          const originalHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await doc.file.arrayBuffer()))).map(x=>x.toString(16).padStart(2,'0')).join('');
          if(hash!==originalHash)throw new Error('Migration verification failed');
          succeeded++;
        }catch{failed++;}
      }
      setCloudNotice(`Migration verified: ${succeeded} succeeded; ${failed} failed. Local originals retained. Retry failed files individually.`);
      return {failed};
    },result=>result.failed>0);});
  }
  async function retryCloudDocument(id:string){
    const document=documentsRef.current.find(d=>d.id===id);
    const uid=account.current;
    if(!cloudEnabled&&!document?.cloud){setCloudNotice('Enable cloud storage or use explicit local migration before uploading.');return;}
    if(document&&uid){
      if(document.cloud?.state==='save-failed'){
        saveCloudEdit(id,document.metadata,document.status);
      }else await enqueue(()=>uploadOne(document,uid));
    }
  }
  async function loadDocumentFile(id:string){
    const document=documentsRef.current.find(d=>d.id===id);
    if(!document||document.url)return document;
    const uid=account.current;
    if(!uid||document.ownerUid!==uid)return;
    setCloudNotice('Downloading document…');
    try{
      const blob=await cloudDocuments.file(id,uid);
      if(account.current!==uid)return;
      const file=new File([blob],document.file.name,{type:document.file.type});
      const latest=documentsRef.current.find(d=>d.id===id&&d.ownerUid===uid);
      if(!latest)return;
      const value={...latest,file,url:URL.createObjectURL(file)};
      replaceDocument(value);setCloudNotice('Document ready for preview.');return value;
    }catch(error){setCloudNotice(error instanceof Error?error.message:'Download failed');}
  }
  async function clearCloudDocuments(){
    if(!window.confirm('Permanently delete THIS account’s cloud Vault files, metadata and matching local copies? Passport preparations remain and will show missing-document warnings.'))return;
    await enqueue(async()=>{
      const uid=account.current;
      if(!uid)return;
      const result=await cloudDocuments.clear(uid);
      if(account.current!==uid)return;
      const ids=new Set(result.deleted);
      ids.forEach(id=>deletedIds.current.add(id));
      setDocuments(old=>{old.filter(d=>ids.has(d.id)).forEach(d=>URL.revokeObjectURL(d.url));return old.filter(d=>!ids.has(d.id));});
      const remaining=documentsRef.current.filter(d=>!ids.has(d.id));
      await persistQueue.current.catch(()=>{});await deleteVaultIds(result.deleted);await saveVault(remaining);
      setCloudNotice(`Cloud deletion: ${result.deleted.length} deleted; ${result.failed.length} failed. Failed records retained; retry.`);
    });
  }

  useEffect(() => {
    let cancelled = false;
    async function hydrate() {
      try {
        if (persistenceEnabledRef.current) {
          const stored = await readVault();
          if (cancelled || !persistenceEnabledRef.current) return;
          setDocuments(previous=>{const incoming=stored.filter(d => d && typeof d.id==='string' && d.file instanceof File && d.metadata && typeof d.metadata==='object' && ['self','parent-guardian','spouse','other'].includes(d.metadata.holder) && ['identity','address','birth','education','employment','other'].includes(d.metadata.category) && typeof d.metadata.documentType==='string' && (!d.metadata.categories||Array.isArray(d.metadata.categories)) && (!d.metadata.printedName||typeof d.metadata.printedName==='string') && (!d.metadata.residentialAddress||typeof d.metadata.residentialAddress==='string') && ['reviewed','needs-review'].includes(d.status) && Number.isFinite(d.addedAt)&&(!d.ownerUid||d.ownerUid===account.current)).map(d => ({
            ...d, file: d.file as File, addedAt: new Date(d.addedAt), url: URL.createObjectURL(d.file),
          }));
          const merged=new Map(incoming.map(d=>[d.id,d]));
          previous.forEach(d=>merged.set(d.id,d));
          return [...merged.values()];});
        }
      } catch (err) { if (!cancelled) setPersistenceError(`Local Vault could not be restored: ${String(err)}`); }
      finally { if (!cancelled) { hydrated.current = true; setPersistenceReady(true); } }
    }
    void hydrate();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!hydrated.current || !persistenceEnabled) return;

    const snapshot = documents;
    const cacheGeneration=cacheEpoch.current;

    persistQueue.current = persistQueue.current
      .catch(() => { })
      .then(async () => {
        if (persistenceEnabledRef.current&&cacheGeneration===cacheEpoch.current) {
          await saveVault(snapshot.filter(d=>!deletedIds.current.has(d.id)));
        }
      })
      .catch((err) => {
        setPersistenceError(`Local Vault save failed: ${String(err)}`);
      });
  }, [documents, persistenceEnabled]);

  async function setLocalPersistence(enabled: boolean) {
    setPersistenceError("");
    if (!persistenceReady) return;
    if (enabled) {
      try { localStorage.setItem(PREF, "yes"); }
      catch { setPersistenceError('Browser storage is unavailable. Vault remains in this session.'); return; }
      persistenceEnabledRef.current = true;
      setPersistenceEnabled(true);
      // Save the current session immediately; no upload to a server.
      persistQueue.current = persistQueue.current.catch(() => { }).then(() => saveVault(documentsRef.current));
      try { await persistQueue.current; } catch (err) {
        persistenceEnabledRef.current=false;setPersistenceEnabled(false);
        try { localStorage.removeItem(PREF); } catch { /* Storage already unavailable. */ }
        setPersistenceError(`Local Vault save failed: ${String(err)}`);
      }
    } else {
      persistenceEnabledRef.current = false;
      setPersistenceEnabled(false);
      try { localStorage.removeItem(PREF); }
      catch { setPersistenceError('Could not remove the Vault saving preference. Check browser permissions.'); }
      try { await persistQueue.current.catch(() => { }); await deleteVault(); }
      catch (err) { setPersistenceError(`Local Vault deletion failed: ${String(err)}`); }
    }
  }

  async function clearAllDocuments() {
    cacheEpoch.current++;
    const existing = documentsRef.current;

    // Serialize deletion after all previously queued saves.
    // This prevents older snapshots from overwriting the cleared Vault.
    const clearOperation = persistQueue.current
      .catch(() => { })
      .then(async () => {
        await deleteVault();
      });

    persistQueue.current = clearOperation;

    try {
      await clearOperation;
      // Show the empty state only once deletion has committed. Otherwise a
      // reload immediately after the UI clears can restore the old records.
      documentsRef.current = [];
      setDocuments([]);
      existing.forEach((document) => URL.revokeObjectURL(document.url));
    } catch (err) {
      // A browser denying IndexedDB must still allow removal of session data.
      documentsRef.current=[];
      setDocuments([]);
      existing.forEach(document=>URL.revokeObjectURL(document.url));
      setPersistenceError(`Session documents cleared, but browser-local deletion failed: ${String(err)}. Use browser site-data settings to remove any stored copies.`);
    }
  }


  useLayoutEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  useEffect(() => {
    return () => {
      documentsRef.current.forEach((document) => URL.revokeObjectURL(document.url));
    };
  }, []);

  async function addDocuments(incoming: LocalDocument[]) {
    const uid=account.current;
    const bound=incoming.map(d=>({...d,...(uid?{ownerUid:uid}:{})}));
    setDocuments((previous) => [...previous, ...bound]);
    if(cloudEnabled&&uid)await enqueue(async()=>{for(const document of bound)await uploadOne(document,uid);});
  }

  function removeLocalDocument(id: string) {
    const found = documentsRef.current.find((document) => document.id === id);
    if (!found) return;
    deletedIds.current.add(id);
    setDocuments((previous) => previous.filter((document) => document.id !== id));
    URL.revokeObjectURL(found.url);
    persistQueue.current=persistQueue.current.catch(()=>{}).then(()=>deleteVaultIds([id])).catch(()=>setPersistenceError('Document removed from session; browser cache deletion failed. Retry clearing local copies.'));
  }

  function toggleLocalReviewed(id: string) {
    setDocuments((previous) =>
      previous.map((document) =>
        document.id === id
          ? {
            ...document,
            status: document.status === "reviewed" ? "needs-review" : "reviewed",
          }
          : document,
      ),
    );
  }

  function updateLocalMetadata(id: string, metadata: DocumentMetadata) {
    setDocuments((previous) =>
      previous.map((document) =>
        document.id === id ? { ...document, metadata: { ...metadata } } : document,
      ),
    );
  }

  function removeDocument(id:string){
    const document=documentsRef.current.find(d=>d.id===id);
    if(document?.cloud){
      if(!window.confirm('Delete this cloud document and its local copy?'))return;
      void enqueue(async()=>{await cloudDocuments.remove(id,document.cloud!.revision,document.ownerUid);if(document.ownerUid===account.current){deletedIds.current.add(id);removeLocalDocument(id);setCloudNotice('Cloud document deleted.');}});
    }else removeLocalDocument(id);
  }
  function saveCloudEdit(id:string,metadata:DocumentMetadata,status:LocalDocument['status']){
    void enqueue(async()=>{
      const document=documentsRef.current.find(d=>d.id===id);
      if(!document?.cloud||document.ownerUid!==account.current)return;
      const revisionKey=`${document.ownerUid}:${id}`;
      const revision=acknowledgedRevisions.current.get(revisionKey)??document.cloud.revision;
      setDocuments(old=>old.map(d=>d.id===id&&d.cloud?{...d,cloud:{...d.cloud,state:'saving'}}:d));
      try{
        const record=await cloudDocuments.patch(id,revision,metadata,status,document.ownerUid);
        if(document.ownerUid!==account.current)return;
        acknowledgedRevisions.current.set(revisionKey,record.revision);
        // Apply server revision/timestamps only. An older acknowledgment must
        // never replace fields or review status changed during the request.
        setDocuments(old=>old.map(d=>d.id===id&&d.cloud?{...d,updatedAt:record.updatedAt,cloud:{...d.cloud,revision:record.revision,state:d.metadata===metadata&&d.status===status?'ready':'save-failed'}}:d));
        setCloudNotice('Reviewed metadata saved to cloud. Compare documents or continue Passport.');
      }catch(error){
        setDocuments(old=>old.map(d=>d.id===id&&d.cloud?{...d,cloud:{...d.cloud,state:'save-failed'}}:d));
        throw error;
      }
    });
  }
  function updateMetadata(id:string,metadata:DocumentMetadata){
    const document=documentsRef.current.find(d=>d.id===id);
    updateLocalMetadata(id,metadata);
    if(document?.cloud)saveCloudEdit(id,metadata,document.status);
  }
  function toggleReviewed(id:string){
    const document=documentsRef.current.find(d=>d.id===id);
    toggleLocalReviewed(id);
    if(document?.cloud)saveCloudEdit(id,document.metadata,document.status==='reviewed'?'needs-review':'reviewed');
  }
  return (
    <DocumentContext.Provider
      value={{
        documents, addDocuments, removeDocument, toggleReviewed, updateMetadata,
        persistenceEnabled, persistenceReady, persistenceError, setLocalPersistence, clearAllDocuments,
        cloudBusy,cloudNotice,cloudEnabled,enableCloudStorage,migrateLocalDocuments,loadDocumentFile,retryCloudDocument,clearCloudDocuments
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
}
