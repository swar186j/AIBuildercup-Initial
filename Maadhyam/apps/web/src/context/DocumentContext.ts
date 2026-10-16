import { createContext, useContext } from "react";

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

export type DocumentContextValue = {
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

export const DocumentContext = createContext<DocumentContextValue | null>(null);

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
