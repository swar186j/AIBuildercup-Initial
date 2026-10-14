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
  printedName?: string;
  dateOfBirth?: string; // YYYY-MM-DD when entered manually
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
      docs.forEach(({url: _url, addedAt, ...rest}) => store.put({...rest, addedAt: addedAt.getTime()}));
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
  const [persistenceEnabled, setPersistenceEnabled] = useState(() => localStorage.getItem(PREF) === "yes");
  const [persistenceReady, setPersistenceReady] = useState(false);
  const [persistenceError, setPersistenceError] = useState("");
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
          setDocuments(stored.filter(d => d.file instanceof Blob).map(d => ({
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
    persistQueue.current = persistQueue.current.catch(() => {}).then(async () => {
      if (persistenceEnabledRef.current) await saveVault(snapshot);
    }).catch(err => setPersistenceError(`Local Vault save failed: ${String(err)}`));
  }, [documents, persistenceEnabled]);

  async function setLocalPersistence(enabled: boolean) {
    setPersistenceError("");
    if (!persistenceReady) return;
    if (enabled) {
      localStorage.setItem(PREF, "yes");
      persistenceEnabledRef.current = true;
      setPersistenceEnabled(true);
      // Save the current session immediately; no upload to a server.
      persistQueue.current = persistQueue.current.catch(() => {}).then(() => saveVault(documentsRef.current));
      try { await persistQueue.current; } catch (err) { setPersistenceError(`Local Vault save failed: ${String(err)}`); }
    } else {
      persistenceEnabledRef.current = false;
      localStorage.removeItem(PREF);
      setPersistenceEnabled(false);
      try { await persistQueue.current.catch(() => {}); await deleteVault(); }
      catch (err) { setPersistenceError(`Local Vault deletion failed: ${String(err)}`); }
    }
  }

  async function clearAllDocuments() {
    const existing = documentsRef.current;
    documentsRef.current = [];
    setDocuments([]);
    existing.forEach(d => URL.revokeObjectURL(d.url));
    try { await persistQueue.current.catch(() => {}); await deleteVault(); }
    catch (err) { setPersistenceError(`Local Vault deletion failed: ${String(err)}`); }
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
      value={{ documents, addDocuments, removeDocument, toggleReviewed, updateMetadata,
        persistenceEnabled, persistenceReady, persistenceError, setLocalPersistence, clearAllDocuments }}
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
