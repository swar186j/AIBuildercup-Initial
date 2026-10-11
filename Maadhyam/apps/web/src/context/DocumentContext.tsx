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

type DocumentContextValue = {
  documents: LocalDocument[];
  addDocuments: (documents: LocalDocument[]) => void;
  removeDocument: (id: string) => void;
  toggleReviewed: (id: string) => void;
  updateMetadata: (id: string, metadata: DocumentMetadata) => void;
};

const DocumentContext = createContext<DocumentContextValue | null>(null);

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<LocalDocument[]>([]);
  const documentsRef = useRef<LocalDocument[]>([]);

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
      value={{ documents, addDocuments, removeDocument, toggleReviewed, updateMetadata }}
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
