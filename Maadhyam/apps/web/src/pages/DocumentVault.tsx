import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react";
import {
  useDocuments,
  getDocumentCategories,
  type DocumentCategory,
  type DocumentHolder,
  type DocumentMetadata,
  type LocalDocument,
} from "../context/DocumentContext";
import {
  CheckCircle2,
  Eye,
  FileImage,
  FileSearch,
  FileText,
  FolderOpen,
  Info,
  LockKeyhole,
  Pencil,
  Search,
  ShieldAlert,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";

type DocumentFilter = "all" | "needs-review" | "reviewed";
const categories: { value: DocumentCategory; label: string }[] = [
  { value: "identity", label: "Identity proof" },
  { value: "address", label: "Address proof" },
  { value: "birth", label: "Date of birth" },
  { value: "education", label: "Education" },
  { value: "employment", label: "Employment" },
  { value: "other", label: "Other / Unclassified" },
];
const holders: { value: DocumentHolder; label: string }[] = [
  { value: "self", label: "Self" },
  { value: "parent-guardian", label: "Parent / Guardian" },
  { value: "spouse", label: "Spouse" },
  { value: "other", label: "Other" },
];
const documentTypes: Record<DocumentCategory, string[]> = {
  identity: ["Aadhaar card", "PAN card", "Voter ID", "Driving licence", "Passport", "Other identity document"],
  address: ["Aadhaar card", "Voter ID", "Utility bill", "Bank statement", "Rental agreement", "Other address document"],
  birth: ["Birth certificate", "School leaving certificate", "Other date-of-birth document"],
  education: ["Marksheet", "Degree certificate", "Diploma", "Other education document"],
  employment: ["Employment letter", "Payslip", "Experience letter", "Other employment document"],
  other: ["Unclassified", "Other document"],
};
const defaultMetadata: DocumentMetadata = {
  category: "other",
  categories: ["other"],
  documentType: "Unclassified",
  holder: "self",
};
function categoryLabel(category: DocumentCategory) {
  return categories.find((item) => item.value === category)?.label ?? "Other";
}
function holderLabel(holder: DocumentHolder) {
  return holders.find((item) => item.value === holder)?.label ?? "Other";
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/png"];
const filters: { id: DocumentFilter; label: string }[] = [
  { id: "all", label: "All documents" },
  { id: "needs-review", label: "Needs review" },
  { id: "reviewed", label: "Self-reviewed" },
];

function formatSize(bytes: number): string {
  return bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(1)} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isSupportedFile(file: File): boolean {
  const extension = file.name.split(".").pop()?.toLowerCase();
  const validExtension = extension === "pdf" || extension === "jpg" || extension === "jpeg" || extension === "png";
  return validExtension && (ACCEPTED_TYPES.includes(file.type) || file.type === "");
}

export default function DocumentVault() {
  const { documents, addDocuments, removeDocument: removeStoredDocument, toggleReviewed, updateMetadata } = useDocuments();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<DocumentFilter>("all");
  const [dragging, setDragging] = useState(false);
  const [message, setMessage] = useState("");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [draftMetadata, setDraftMetadata] = useState<DocumentMetadata>(defaultMetadata);
  const [categoryFilter, setCategoryFilter] = useState<DocumentCategory | "all">("all");
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (previewId === null && editId === null) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") { setPreviewId(null); setEditId(null); }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [previewId, editId]);

  function addFiles(fileList: FileList | File[]) {
    const accepted: LocalDocument[] = [];
    const errors: string[] = [];

    for (const file of Array.from(fileList)) {
      if (!isSupportedFile(file)) {
        errors.push(`${file.name}: only PDF, JPG and PNG files are supported.`);
      } else if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: file exceeds the 10 MB limit.`);
      } else if (file.size === 0) {
        errors.push(`${file.name}: empty files cannot be added.`);
      } else {
        accepted.push({
          id: crypto.randomUUID(),
          file,
          url: URL.createObjectURL(file),
          status: "needs-review",
          addedAt: new Date(),
          metadata: { ...defaultMetadata },
        });
      }
    }

    if (accepted.length) addDocuments(accepted);
    setMessage(
      [
        accepted.length ? `${accepted.length} file${accepted.length === 1 ? "" : "s"} added to this browser session.` : "",
        ...errors,
      ]
        .filter(Boolean)
        .join(" "),
    );
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) addFiles(event.target.files);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    setDragging(false);
    if (event.dataTransfer.files.length) addFiles(event.dataTransfer.files);
  }

  function removeDocument(id: string) {
    const document = documents.find((item) => item.id === id);
    if (!document) return;
    if (previewId === id) setPreviewId(null);
    if (editId === id) setEditId(null);
    removeStoredDocument(id);
    setMessage(`${document.file.name} removed from this browser session.`);
  }

  function openEdit(document: LocalDocument) {
    setDraftMetadata({ ...document.metadata, categories: getDocumentCategories(document.metadata) });
    setEditId(document.id);
  }

  function saveMetadata() {
    if (!editId) return;
    updateMetadata(editId, { ...draftMetadata, categories: getDocumentCategories(draftMetadata) });
    setEditId(null);
    setMessage("Document details updated in this browser session.");
  }

  const needsReview = documents.filter((document) => document.status === "needs-review").length;
  const reviewed = documents.filter((document) => document.status === "reviewed").length;
  const filtered = documents.filter((document) => {
    const matchesStatus = filter === "all" || document.status === filter;
    const matchesCategory = categoryFilter === "all" || getDocumentCategories(document.metadata).includes(categoryFilter);
    const searchText = [document.file.name, getDocumentCategories(document.metadata).map(categoryLabel).join(" "), document.metadata.documentType, holderLabel(document.metadata.holder)].join(" ").toLowerCase();
    const matchesQuery = searchText.includes(query.trim().toLowerCase());
    return matchesStatus && matchesCategory && matchesQuery;
  });
  const preview = documents.find((document) => document.id === previewId);

  return (
    <div className="mx-auto max-w-6xl space-y-7 pb-24">
      <div>
        <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">Document workspace</p>
        <h1 className="mt-2 text-3xl font-bold text-[#173f68]">Document Vault</h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Organize and preview documents for government-service preparation. Files stay in this browser session only.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Total documents", count: documents.length, icon: FileText },
          { label: "Needs review", count: needsReview, icon: ShieldAlert },
          { label: "Self-reviewed", count: reviewed, icon: FileSearch },
        ].map(({ label, count, icon: Icon }) => (
          <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-slate-600">{label}</span>
              <Icon size={20} className="text-[#147d83]" aria-hidden="true" />
            </div>
            <p className="mt-4 text-3xl font-bold text-[#173f68]">{count}</p>
          </div>
        ))}
      </div>

      <section
        onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={(event) => {
          event.preventDefault();
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
        }}
        onDrop={onDrop}
        className={`rounded-2xl border-2 border-dashed px-6 py-10 text-center transition sm:px-10 ${
          dragging ? "border-[#147d83] bg-[#e4f3f1]" : "border-[#9dcacb] bg-[#f2f8f8]"
        }`}
      >
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-[#147d83] shadow-sm">
          <UploadCloud size={27} aria-hidden="true" />
        </div>
        <h2 className="mt-4 text-xl font-bold text-[#173f68]">Add documents for preview</h2>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">
          Drag files here or select PDFs, JPGs and PNGs (up to 10 MB each). This is a local prototype, not secure cloud storage.
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
          multiple
          onChange={onFileChange}
          className="sr-only"
          aria-label="Choose documents to add"
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#126a70] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83]"
        >
          <UploadCloud size={18} /> Choose files
        </button>
        <div className="mt-5 flex items-center justify-center gap-2 text-xs text-slate-500">
          <LockKeyhole size={15} aria-hidden="true" />
          Files are not sent to the Maadhyam backend. Refreshing the page clears this list.
        </div>
        {message && <p role="status" className="mx-auto mt-4 max-w-xl text-sm text-[#173f68]">{message}</p>}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-bold text-[#173f68]">Your documents</h2>
            <p className="mt-1 text-sm text-slate-500">Temporary files added during this session.</p>
          </div>
          <div className="relative w-full lg:max-w-xs">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search documents..."
              aria-label="Search documents"
              className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm outline-none focus:border-[#147d83]"
            />
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2" role="group" aria-label="Document status filter">
          {filters.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={filter === item.id}
              onClick={() => setFilter(item.id)}
              className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                filter === item.id ? "bg-[#147d83] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label htmlFor="document-category-filter" className="text-sm font-medium text-slate-600">Category</label>
          <select
            id="document-category-filter"
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value as DocumentCategory | "all")}
            className="max-w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-[#173f68] outline-none focus:border-[#147d83]"
          >
            <option value="all">All categories</option>
            {categories.map((category) => <option key={category.value} value={category.value}>{category.label}</option>)}
          </select>
        </div>

        {filtered.length === 0 ? (
          <div className="mt-6 rounded-xl border border-slate-100 bg-slate-50 px-5 py-12 text-center">
            <FolderOpen size={36} className="mx-auto text-slate-400" aria-hidden="true" />
            <h3 className="mt-4 font-semibold text-[#173f68]">
              {documents.length === 0 ? "No documents yet" : "No matching documents"}
            </h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
              {documents.length === 0
                ? "Add a sample PDF or image to preview it here."
                : "Try another search term or document status filter."}
            </p>
          </div>
        ) : (
          <div className="mt-6 grid gap-3">
            {filtered.map((document) => {
              const isPdf = document.file.name.toLowerCase().endsWith(".pdf");
              return (
                <article key={document.id} className="flex flex-col gap-4 rounded-xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex min-w-0 items-start gap-3">
                    <div className="rounded-xl bg-[#edf5f4] p-3 text-[#147d83]">
                      {isPdf ? <FileText size={22} /> : <FileImage size={22} />}
                    </div>
                    <div className="min-w-0">
                      <h3 className="break-all text-sm font-semibold text-[#173f68]">{document.file.name}</h3>
                      <p className="mt-1 text-xs text-slate-500">
                        {isPdf ? "PDF" : "Image"} · {formatSize(document.file.size)} · {document.addedAt.toLocaleString()}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                          document.status === "reviewed" ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"
                        }`}>
                          {document.status === "reviewed" ? "Self-reviewed" : "Needs review"}
                        </span>
                        {getDocumentCategories(document.metadata).map((category) => (
                          <span key={category} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700">
                            {categoryLabel(category)}
                          </span>
                        ))}
                        <span className="text-xs text-slate-500">
                          {document.metadata.documentType} · {holderLabel(document.metadata.holder)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 sm:justify-end">
                    <button type="button" onClick={() => setPreviewId(document.id)} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-[#173f68] hover:bg-slate-50">
                      <Eye size={15} /> Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => openEdit(document)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-[#173f68] hover:bg-slate-50"
                    >
                      <Pencil size={15} /> Edit details
                    </button>
                    <button type="button" onClick={() => toggleReviewed(document.id)} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-[#173f68] hover:bg-slate-50">
                      <CheckCircle2 size={15} /> {document.status === "reviewed" ? "Mark for review" : "Mark self-reviewed"}
                    </button>
                    <button type="button" onClick={() => removeDocument(document.id)} aria-label={`Remove ${document.file.name}`} className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-50">
                      <Trash2 size={15} /> Remove
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-xs leading-6 text-slate-600">
        <Info size={18} className="mt-0.5 shrink-0 text-[#147d83]" />
        <p>
          Maadhyam is an independent assistance platform. “Self-reviewed” only means you marked a file as reviewed; it does not indicate authenticity, eligibility, document acceptance or government verification. For now, use dummy documents rather than sensitive personal records.
        </p>
      </div>

      {editId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-3 sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setEditId(null); }}>
          <section role="dialog" aria-modal="true" aria-labelledby="metadata-dialog-title" className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl sm:p-7">
            <div className="flex items-center justify-between gap-3">
              <h2 id="metadata-dialog-title" className="text-xl font-bold text-[#173f68]">Edit document details</h2>
              <button type="button" onClick={() => setEditId(null)} aria-label="Close details" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"><X size={20} /></button>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">Manually classify this file. Categories are for organization only, not proof of official acceptance.</p>
            <form onSubmit={(event) => { event.preventDefault(); saveMetadata(); }} className="mt-6 space-y-5">
              <div>
                <label htmlFor="metadata-type" className="mb-2 block text-sm font-semibold text-[#173f68]">Document type</label>
                <select
                  id="metadata-type"
                  value={draftMetadata.documentType}
                  onChange={(event) => setDraftMetadata((previous) => ({ ...previous, documentType: event.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-[#147d83]"
                >
                  {[...new Set(Object.values(documentTypes).flat())].map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <fieldset>
                <legend className="mb-2 text-sm font-semibold text-[#173f68]">Document purposes (select one or more)</legend>
                <p className="mb-3 text-xs leading-5 text-slate-500">
                  Select how you want to organize this file. These are not official acceptance decisions.
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {categories.map((item) => {
                    const selected = getDocumentCategories(draftMetadata).includes(item.value);
                    return (
                      <label key={item.value} className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 px-3 py-3 text-sm text-[#173f68]">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => {
                            setDraftMetadata((previous) => {
                              const current = getDocumentCategories(previous);
                              let next = selected
                                ? current.filter((category) => category !== item.value)
                                : [...current.filter((category) => category !== "other"), item.value];
                              if (item.value === "other" && !selected) next = ["other"];
                              if (!next.length) next = ["other"];
                              return { ...previous, category: next[0], categories: next };
                            });
                          }}
                          className="h-4 w-4 accent-[#147d83]"
                        />
                        {item.label}
                      </label>
                    );
                  })}
                </div>
              </fieldset>
              <div>
                <label htmlFor="metadata-holder" className="mb-2 block text-sm font-semibold text-[#173f68]">Document holder</label>
                <select id="metadata-holder" value={draftMetadata.holder} onChange={(event) => setDraftMetadata((previous) => ({ ...previous, holder: event.target.value as DocumentHolder }))} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-[#147d83]">
                  {holders.map((holder) => <option key={holder.value} value={holder.value}>{holder.label}</option>)}
                </select>
              </div>
              <div className="flex flex-wrap justify-end gap-3 border-t border-slate-100 pt-5">
                <button type="button" onClick={() => setEditId(null)} className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
                <button type="submit" className="rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white hover:bg-[#126a70]">Save details</button>
              </div>
            </form>
          </section>
        </div>
      )}

      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-3 sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setPreviewId(null); }}>
          <section role="dialog" aria-modal="true" aria-label={`Preview ${preview.file.name}`} className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-6">
              <div className="min-w-0">
                <h2 className="truncate text-sm font-bold text-[#173f68]">{preview.file.name}</h2>
                <p className="text-xs text-slate-500">Local preview only</p>
              </div>
              <button type="button" onClick={() => setPreviewId(null)} aria-label="Close preview" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"><X size={20} /></button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto bg-slate-100 p-3 sm:p-5">
              {preview.file.name.toLowerCase().endsWith(".pdf") ? (
                <iframe src={preview.url} title={`PDF preview: ${preview.file.name}`} className="h-[65vh] w-full rounded-lg bg-white" />
              ) : (
                <img src={preview.url} alt={`Preview of ${preview.file.name}`} className="mx-auto max-h-[65vh] max-w-full rounded-lg object-contain" />
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
