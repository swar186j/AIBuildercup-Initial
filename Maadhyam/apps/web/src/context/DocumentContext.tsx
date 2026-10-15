import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

export type ReviewStatus = "needs-review" | "reviewed";
export type DocumentCategory =
  | "identity"
  | "address"
  | "birth"
  | "education"
  | "employment"
  | "other";
export type DocumentHolder = "self" | "parent-guardian" | "spouse" | "other";

export type DocumentMetadata = {
  category: DocumentCategory;
  categories?: DocumentCategory[]; // Additional manually assigned purposes; legacy category stays primary
  documentType: string;
  holder: DocumentHolder;
  householdMemberId?: string;
  associationConsent?: boolean;
  printedName?: string;
  dateOfBirth?: string; // YYYY-MM-DD when entered manually
  expiryDate?: string; // Optional printed expiry, ISO YYYY-MM-DD
  residentialAddress?: string;
};

export type LocalDocument = {
  id: string;
  file: File;
  url: string;
  status: ReviewStatus;
  addedAt: Date;
  metadata: DocumentMetadata;
};

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
      store.clear();
      docs.forEach(({ url: _url, addedAt, ...rest }) => store.put({ ...rest, addedAt: addedAt.getTime() }));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally { db.close(); }
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

type DocumentContextValue = {
  documents: LocalDocument[];
  addDocuments: (documents: LocalDocument[]) => void;
  removeDocument: (id: string) => void;
  toggleReviewed: (id: string) => void;
  updateMetadata: (id: string, metadata: DocumentMetadata) => void;
  persistenceEnabled: boolean;
  persistenceReady: boolean;
  persistenceError: string;
  setLocalPersistence: (enabled: boolean) => Promise<void>;
  clearAllDocuments: () => Promise<void>;
};

const DocumentContext = createContext<DocumentContextValue | null>(null);

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
  persistenceEnabledRef.current = persistenceEnabled;
  const hydrated = useRef(false);

  useEffect(() => {
    let cancelled = false;
    async function hydrate() {
      try {
        if (persistenceEnabledRef.current) {
          const stored = await readVault();
          if (cancelled || !persistenceEnabledRef.current) return;
          setDocuments(stored.filter(d => d && typeof d.id==='string' && d.file instanceof File && d.metadata && typeof d.metadata==='object' && ['self','parent-guardian','spouse','other'].includes(d.metadata.holder) && ['identity','address','birth','education','employment','other'].includes(d.metadata.category) && typeof d.metadata.documentType==='string' && (!d.metadata.categories||Array.isArray(d.metadata.categories)) && (!d.metadata.printedName||typeof d.metadata.printedName==='string') && (!d.metadata.residentialAddress||typeof d.metadata.residentialAddress==='string') && ['reviewed','needs-review'].includes(d.status) && Number.isFinite(d.addedAt)).map(d => ({
            ...d, file: d.file as File, addedAt: new Date(d.addedAt), url: URL.createObjectURL(d.file),
          })));
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

    persistQueue.current = persistQueue.current
      .catch(() => { })
      .then(async () => {
        if (persistenceEnabledRef.current) {
          await saveVault(snapshot);
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


  useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  useEffect(() => {
    return () => {
      documentsRef.current.forEach((document) => URL.revokeObjectURL(document.url));
    };
  }, []);

  function addDocuments(incoming: LocalDocument[]) {
    setDocuments((previous) => [...previous, ...incoming]);
  }

  function removeDocument(id: string) {
    const found = documentsRef.current.find((document) => document.id === id);
    if (!found) return;
    setDocuments((previous) => previous.filter((document) => document.id !== id));
    URL.revokeObjectURL(found.url);
  }

  function toggleReviewed(id: string) {
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

  function updateMetadata(id: string, metadata: DocumentMetadata) {
    setDocuments((previous) =>
      previous.map((document) =>
        document.id === id ? { ...document, metadata: { ...metadata } } : document,
      ),
    );
  }

  return (
    <DocumentContext.Provider
      value={{
        documents, addDocuments, removeDocument, toggleReviewed, updateMetadata,
        persistenceEnabled, persistenceReady, persistenceError, setLocalPersistence, clearAllDocuments
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocuments(): DocumentContextValue {
  const context = useContext(DocumentContext);
  if (!context) {
    throw new Error("useDocuments must be used inside DocumentProvider");
  }
  return context;
}

// Read both legacy single-category metadata and new multi-category assignments.
export function getDocumentCategories(metadata: DocumentMetadata): DocumentCategory[] {
  const selected = metadata.categories?.length ? metadata.categories : [metadata.category];
  return [...new Set(selected)];
}
