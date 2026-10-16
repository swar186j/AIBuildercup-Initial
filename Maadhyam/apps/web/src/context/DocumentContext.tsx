/* eslint react-refresh/only-export-components: ["error", { "allowExportNames": ["useDocuments", "getDocumentCategories"] }] */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from './AuthContext';
import { auth } from '../services/firebase';
import { listDocuments, restoreDocument, uploadDocument, patchDocument, deleteDocument } from '../services/cloudWorkspace';

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
  pendingDeletion?: boolean;
  id: string;
  file: File;
  url: string;
  status: ReviewStatus;
  addedAt: Date;
  metadata: DocumentMetadata;
};


type DocumentContextValue = {
  documents: LocalDocument[];
  addDocuments: (documents: LocalDocument[]) => Promise<void>;
  removeDocument: (id: string) => void;
  toggleReviewed: (id: string) => void;
  updateMetadata: (id: string, metadata: DocumentMetadata) => void;
  persistenceReady: boolean;
  persistenceError: string;
  cloudBusy: boolean;
  storageNotice: string;
  retryCloud: () => void;
  clearAllDocuments: () => Promise<void>;
};
const DocumentContext = createContext<DocumentContextValue | null>(null);

export function DocumentProvider({ children, accountId }: { children: ReactNode; accountId?: string }) {
  const { registerLogoutGuard } = useAuth();
  const [documents, setDocuments] = useState<LocalDocument[]>([]);
  const current = useRef<LocalDocument[]>([]);
  const revisions = useRef(new Map<string, number>());
  const queues = useRef(new Map<string, Promise<void>>());
  const failed = useRef(new Map<string, () => Promise<void>>());
  const [failureCount, setFailureCount] = useState(0);
  const session = useRef(0);
  const [persistenceReady, setReady] = useState(false);
  const [persistenceError, setError] = useState('');
  const [storageNotice, setNotice] = useState('Loading your cloud documents…');
  const [busy, setBusy] = useState(0);
  const [reload, setReload] = useState(0);
  const assign = useCallback((next: LocalDocument[]) => { current.current = next; setDocuments(next); }, []);

  useEffect(() => registerLogoutGuard(() => busy === 0 && failureCount === 0), [registerLogoutGuard, busy, failureCount]);
  useEffect(() => {
    if (!busy && !failureCount) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [busy, failureCount]);

  useEffect(() => {
    const generation = ++session.current;
    const restored: LocalDocument[] = [];
    void (async () => {
      setReady(false); setError('');
      try {
        const records = await listDocuments();
        for (const record of records) {
          if (generation !== session.current) return;
          const document = await restoreDocument(record);
          restored.push(document);
          if (generation !== session.current) { URL.revokeObjectURL(document.url); return; }
          revisions.current.set(record.id, record.revision);
        }
        if (generation !== session.current) return;
        assign(restored);
        setReady(true); setNotice('Documents saved privately to your account.');
      } catch (error) {
        restored.forEach(document => URL.revokeObjectURL(document.url));
        if (generation === session.current) setError(error instanceof Error ? error.message : 'Cloud documents could not load.');
      }
    })();
    return () => {
      session.current += 1;
      current.current.forEach(document => URL.revokeObjectURL(document.url));
    };
  }, [accountId, assign, reload]);

  function enqueue(id: string, operation: () => Promise<void>): Promise<void> {
    const generation = session.current;
    setBusy(count => count + 1); setError('');
    const next = (queues.current.get(id) || Promise.resolve()).catch(() => {}).then(async () => {
      if (generation !== session.current || auth?.currentUser?.uid !== accountId) return;
      await operation();
      if (generation !== session.current) return;
      failed.current.delete(id); setFailureCount(failed.current.size);
      setNotice('Cloud changes saved.');
    }).catch(error => {
      if (generation !== session.current) return;
      failed.current.set(id, operation); setFailureCount(failed.current.size);
      setError(error instanceof Error ? error.message : 'Cloud save failed.');
      throw error;
    }).finally(() => {
      if (generation === session.current) setBusy(count => Math.max(0, count - 1));
      if (queues.current.get(id) === next) queues.current.delete(id);
    });
    queues.current.set(id, next);
    return next;
  }
  async function addDocuments(incoming: LocalDocument[]) {
    if (!persistenceReady) throw new Error('Wait for cloud documents to load.');
    const uploads = incoming.map(document => {
      const generation = session.current;
      return enqueue(document.id, async () => {
        const saved = await uploadDocument(document);
        if (generation !== session.current) return;
        revisions.current.set(document.id, saved.revision);
        if (!current.current.some(item => item.id === document.id)) assign([...current.current, document]);
      });
    });
    const results = await Promise.allSettled(uploads);
    const rejected = results.find(result => result.status === 'rejected');
    if (rejected?.status === 'rejected') throw rejected.reason;
  }
  function updateDocument(id: string, transform: (document: LocalDocument) => LocalDocument) {
    const generation = session.current;
    void enqueue(id, async () => {
      const previous = current.current.find(document => document.id === id);
      if (!previous) return;
      const next = transform(previous);
      const result = await patchDocument(next, revisions.current.get(id)!);
      if (generation !== session.current) return;
      revisions.current.set(id, result.revision);
      assign(current.current.map(document => document.id === id ? { ...next, metadata: result.metadata, status: result.status } : document));
    }).catch(() => {});
  }
  function removeDocument(id: string) {
    const generation = session.current;
    return enqueue(id, async () => {
      const previous = current.current.find(document => document.id === id);
      if (!previous) return;
      await deleteDocument(id, revisions.current.get(id)!);
      if (generation !== session.current) return;
      assign(current.current.filter(document => document.id !== id));
      revisions.current.delete(id); URL.revokeObjectURL(previous.url);
    });
  }
  async function clearAllDocuments() {
    for (const document of [...current.current]) await removeDocument(document.id);
  }
  function retryCloud() {
    if (!persistenceReady) { setReload(value => value + 1); return; }
    for (const [id, operation] of failed.current) void enqueue(id, operation).catch(() => {});
  }
  return <DocumentContext.Provider value={{ documents, addDocuments,
    removeDocument: id => { void removeDocument(id).catch(() => {}); },
    toggleReviewed: id => updateDocument(id, document => ({ ...document, status: document.status === 'reviewed' ? 'needs-review' : 'reviewed' })),
    updateMetadata: (id, metadata) => updateDocument(id, document => ({ ...document, metadata })),
    persistenceReady, persistenceError, cloudBusy: busy > 0, storageNotice, retryCloud, clearAllDocuments,
  }}>{children}</DocumentContext.Provider>;
}
export function useDocuments(): DocumentContextValue {
  const context = useContext(DocumentContext);
  if (!context) throw new Error('Document workspace unavailable');
  return context;
}
export function getDocumentCategories(metadata: DocumentMetadata): DocumentCategory[] {
  const selected = metadata.categories?.length ? metadata.categories : [metadata.category];
  return [...new Set(selected)];
}
