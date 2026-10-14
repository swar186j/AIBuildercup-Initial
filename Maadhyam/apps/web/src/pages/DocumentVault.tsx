import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { extractDocument } from "../services/documentExtraction";
import {
  useDocuments,
  getDocumentCategories,
  type DocumentCategory,
  type DocumentHolder,
  type DocumentMetadata,
  type LocalDocument,
} from "../context/DocumentContext";
import {
  AlertTriangle,
  CheckCircle2,
  GitCompareArrows,
  Sparkles,
  LoaderCircle,
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

import { compareDocuments, type ComparisonResult } from "../utils/documentComparison";

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
  printedName: "",
  dateOfBirth: "",
  residentialAddress: "",
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
  const { documents, addDocuments, removeDocument: removeStoredDocument, toggleReviewed, updateMetadata, persistenceEnabled, persistenceReady, persistenceError, setLocalPersistence, clearAllDocuments } = useDocuments();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<DocumentFilter>("all");
  const [dragging, setDragging] = useState(false);
  const [message, setMessage] = useState("");
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [draftMetadata, setDraftMetadata] = useState<DocumentMetadata>(defaultMetadata);
  const [categoryFilter, setCategoryFilter] = useState<DocumentCategory | "all">("all");
  const [analysis, setAnalysis] = useState<ComparisonResult | null>(null);
  const [extractId, setExtractId] = useState<string | null>(null);
  const [demoPhase, setDemoPhase] = useState<"idle" | "processing" | "ready">("idle");
  const [demoDraft, setDemoDraft] = useState<DocumentMetadata>(defaultMetadata);
  const extractionAbort = useRef<AbortController | null>(null);
  const [extractionError, setExtractionError] = useState("");
  const [fictionalConfirmed, setFictionalConfirmed] = useState(false);
  const [extractionWarnings, setExtractionWarnings] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (previewId === null && editId === null && extractId === null) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") { setPreviewId(null); setEditId(null); closeDemo(); }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [previewId, editId, extractId]);

  useEffect(() => () => { extractionAbort.current?.abort(); }, []);

  function closeDemo() {
    extractionAbort.current?.abort();
    extractionAbort.current = null;
    setExtractionError("");
    setExtractionWarnings([]);
    setFictionalConfirmed(false);
    setExtractId(null);
    setDemoPhase("idle");
  }

  function openDemo(document: LocalDocument) {
    setExtractId(document.id);
    setFictionalConfirmed(false);
    setDemoPhase("idle");
    setDemoDraft({ ...document.metadata });
    setExtractionError("");
    setExtractionWarnings([]);
  }

  async function generateDemo() {
    if (!extractId || !fictionalConfirmed) return;
    const target = documents.find((document) => document.id === extractId);
    if (!target) return;
    const controller = new AbortController();
    extractionAbort.current?.abort();
    extractionAbort.current = controller;
    setExtractionError("");
    setExtractionWarnings([]);
    setDemoPhase("processing");
    try {
      const result = await extractDocument(target.file, controller.signal);
      if (controller.signal.aborted) return;
      const proposedCategories = result.categories.filter((category) => category !== "other");
      setDemoDraft({
        ...target.metadata,
        documentType: result.documentType || target.metadata.documentType,
        printedName: result.printedName ?? "",
        dateOfBirth: result.dateOfBirth ?? "",
        residentialAddress: result.residentialAddress ?? "",
        ...(proposedCategories.length ? { category: proposedCategories[0], categories: proposedCategories } : {}),
      });
      setExtractionWarnings(result.warnings);
      setDemoPhase("ready");
    } catch (error) {
      if (controller.signal.aborted) return;
      setExtractionError(error instanceof Error ? error.message : "Extraction failed. Please try again.");
      setDemoPhase("idle");
    } finally {
      if (extractionAbort.current === controller) extractionAbort.current = null;
    }
  }

  function applyDemo() {
    if (!extractId || demoPhase !== "ready") return;
    updateMetadata(extractId, {
      ...demoDraft,
      printedName: demoDraft.printedName?.trim() ?? "",
      residentialAddress: demoDraft.residentialAddress?.trim() ?? "",
    });
    closeDemo();
    setMessage("AI-extracted details saved after your review. Verify them against the original document.");
  }

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
    if (extractId === id) closeDemo();
    removeStoredDocument(id);
    setMessage(`${document.file.name} removed from this browser session.`);
  }

  function openEdit(document: LocalDocument) {
    setDraftMetadata({ ...document.metadata, categories: getDocumentCategories(document.metadata) });
    setEditId(document.id);
  }

  function saveMetadata() {
    if (!editId) return;
    updateMetadata(editId, {
      ...draftMetadata,
      categories: getDocumentCategories(draftMetadata),
      printedName: draftMetadata.printedName?.trim() ?? "",
      residentialAddress: draftMetadata.residentialAddress?.trim() ?? "",
    });
    setEditId(null);
    setMessage("Document details updated in this browser session.");
  }

  // Analysis results are derived from the current metadata, so edits and removals
  // cannot leave stale findings visible.
  const currentAnalysis = analysis === null ? null : compareDocuments(documents);

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
    <div className="mx-auto w-full max-w-[1560px] space-y-7 pb-24">
      <div>
        <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">Document workspace</p>
        <h1 className="mt-2 text-3xl font-bold text-[#173f68]">Document Vault</h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">
          Organize and preview documents for government-service preparation. Files stay in this browser session unless you explicitly enable browser-local saving.
        </p>
      </div>

      <section aria-label="Local Vault storage controls" className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-semibold text-[#173f68]">Browser-local Vault storage</p>
            <p className="mt-1 text-sm text-slate-600">Off by default. When enabled, files and manually reviewed identity fields remain in this browser after refresh. Not encrypted; use fictional documents for demos. Nothing is uploaded by this storage feature.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={!persistenceReady} onClick={() => void setLocalPersistence(!persistenceEnabled)}
              className="rounded-lg border border-[#147d83] px-4 py-2 text-sm font-semibold text-[#147d83] disabled:opacity-50">
              {persistenceEnabled ? "Disable local saving" : "Enable local saving"}
            </button>
            <button
              type="button"
              onClick={async () => {
                if (!window.confirm("Delete all Vault documents and saved browser copies?")) {
                  return;
                }

                await clearAllDocuments();
              }}
              className="rounded-lg border border-red-300 px-4 py-2 text-sm font-semibold text-red-700">Clear all Vault data</button>
          </div>
        </div>
        {persistenceError && <p role="alert" className="mt-2 text-sm text-red-700">{persistenceError}</p>}
      </section>

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
        className={`rounded-2xl border-2 border-dashed px-6 py-10 text-center transition sm:px-10 ${dragging ? "border-[#147d83] bg-[#e4f3f1]" : "border-[#9dcacb] bg-[#f2f8f8]"
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
              className={`rounded-full px-4 py-2 text-xs font-semibold transition ${filter === item.id ? "bg-[#147d83] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
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
                        <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${document.status === "reviewed" ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"
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
                          {(document.metadata.printedName?.trim() || document.metadata.dateOfBirth || document.metadata.residentialAddress?.trim()) && (
                            <span className="ml-2 text-[#147d83]">· Structured details added</span>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 sm:justify-end">
                    <button type="button" onClick={() => setPreviewId(document.id)} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-[#173f68] hover:bg-slate-50">
                      <Eye size={15} /> Preview
                    </button>
                    <button type="button" onClick={() => openDemo(document)} className="inline-flex items-center gap-1.5 rounded-lg border border-[#9dcacb] bg-[#f2f8f8] px-3 py-2 text-xs font-semibold text-[#147d83] hover:bg-[#e4f3f1]">
                      <Sparkles size={15} /> AI extraction
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

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="comparison-heading">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <GitCompareArrows size={22} className="text-[#147d83]" aria-hidden="true" />
              <h2 id="comparison-heading" className="text-lg font-bold text-[#173f68]">Document discrepancy analysis</h2>
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Compare manually entered name, date of birth and address across files in the same holder category.
              This does not read file contents or verify documents.
            </p>
          </div>
          <button
            type="button"
            disabled={documents.length < 2}
            onClick={() => setAnalysis(compareDocuments(documents))}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white hover:bg-[#126a70] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <GitCompareArrows size={18} /> Analyze documents
          </button>
        </div>

        {documents.length < 2 && (
          <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
            Add at least two documents to enable comparison.
          </p>
        )}

        {currentAnalysis && (
          <div className="mt-6 space-y-4" aria-live="polite">
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { label: "Possible differences", value: currentAnalysis.findings.length },
                { label: "Fields compared", value: currentAnalysis.comparableFieldPairs },
                { label: "Fields skipped (missing data)", value: currentAnalysis.skippedFieldPairs },
              ].map((stat) => (
                <div key={stat.label} className="rounded-xl bg-[#f2f8f8] p-4">
                  <p className="text-xs font-medium text-slate-600">{stat.label}</p>
                  <p className="mt-2 text-2xl font-bold text-[#173f68]">{stat.value}</p>
                </div>
              ))}
            </div>

            {currentAnalysis.comparedPairs === 0 ? (
              <p className="rounded-xl border border-slate-200 p-4 text-sm text-slate-600">
                No documents share a holder category. Set matching holders in Edit details before comparing.
              </p>
            ) : currentAnalysis.comparableFieldPairs === 0 ? (
              <p className="rounded-xl border border-slate-200 p-4 text-sm text-slate-600">
                No populated fields can be compared yet. Enter matching fields on at least two documents.
              </p>
            ) : currentAnalysis.findings.length === 0 ? (
              <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <CheckCircle2 size={20} className="shrink-0 text-emerald-700" />
                <p className="text-sm leading-6 text-emerald-900">
                  No differences found in the populated fields compared. This does not confirm document validity or completeness.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-[#173f68]">Possible differences to review</h3>
                {currentAnalysis.findings.map((finding) => (
                  <article key={finding.id} className="rounded-xl border border-amber-200 bg-amber-50/40 p-4 sm:p-5">
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={19} className="mt-0.5 shrink-0 text-amber-700" aria-hidden="true" />
                      <div className="min-w-0 flex-1">
                        <h4 className="font-semibold text-[#173f68]">{finding.title}</h4>
                        <p className="mt-1 text-xs text-slate-600">Holder category: {holderLabel(finding.holder)}</p>
                        <p className="mt-2 text-sm leading-6 text-slate-700">{finding.explanation}</p>
                        <div className="mt-3 grid gap-3 sm:grid-cols-2">
                          {finding.documents.map((item) => (
                            <div key={item.id} className="min-w-0 rounded-lg border border-slate-200 bg-white p-3">
                              <p className="break-all text-xs font-semibold text-[#173f68]">{item.filename}</p>
                              <p className="mt-2 break-words text-sm text-slate-700">{item.value}</p>
                              <button
                                type="button"
                                onClick={() => {
                                  const selected = documents.find((document) => document.id === item.id);
                                  if (selected) openEdit(selected);
                                }}
                                className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#147d83] hover:underline"
                              >
                                <Pencil size={13} /> Edit details
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
            <p className="text-xs leading-5 text-slate-500">
              Holder categories are not unique person identifiers. In particular, Parent / Guardian and Other may include different people.
              Addresses can also differ legitimately. Review original documents before taking action.
            </p>
          </div>
        )}
      </section>

      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-xs leading-6 text-slate-600">
        <Info size={18} className="mt-0.5 shrink-0 text-[#147d83]" />
        <p>
          Maadhyam is an independent assistance platform. “Self-reviewed” only means you marked a file as reviewed; it does not indicate authenticity, eligibility, document acceptance or government verification. For now, use dummy documents rather than sensitive personal records.
        </p>
      </div>

      {extractId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-3 sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeDemo(); }}>
          <section role="dialog" aria-modal="true" aria-labelledby="demo-extraction-title" className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl sm:p-7">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">Gemini document extraction</p>
                <h2 id="demo-extraction-title" className="mt-1 text-xl font-bold text-[#173f68]">Document extraction preview</h2>
              </div>
              <button type="button" onClick={closeDemo} aria-label="Close AI extraction" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"><X size={20} /></button>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">With your consent, the selected file will be sent through Maadhyam’s backend to Google Gemini for extraction. Use fictional documents while testing. AI can make mistakes; review every field before applying. The uploaded file is not saved by this API.</p>
            <p className="mt-3 break-all rounded-xl bg-slate-50 p-3 text-xs text-slate-600">Selected file: {documents.find((document) => document.id === extractId)?.file.name}</p>
            {extractionError && <p role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{extractionError}</p>}
            {extractionWarnings.length > 0 && <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"><strong>Extraction notes:</strong><ul className="mt-2 list-disc pl-5">{extractionWarnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
            <div className="mt-4 rounded-xl border border-[#9dcacb] bg-[#f2f8f8] p-3 text-sm text-slate-700">
              <strong>Fictional test documents only.</strong> Never upload real Aadhaar, PAN, passport or other confidential documents to this free-tier Gemini demo.
              To enter details without AI, close this dialog and use Edit Details.
            </div>
            <label className="mt-4 flex items-start gap-2 text-sm text-slate-700"><input type="checkbox" className="mt-1" checked={fictionalConfirmed} onChange={(event) => setFictionalConfirmed(event.target.checked)} /> I confirm this is a fictional test document and consent to sending it to Google Gemini. Free-tier provider data-use policies may apply.</label>
            {demoPhase === "idle" && (
              <div className="mt-6 space-y-4">
                <p className="text-sm text-slate-600">The document will be transmitted to Google Gemini only when you select Extract with Gemini.</p>
                <button type="button" onClick={generateDemo} disabled={!fictionalConfirmed} className="inline-flex disabled:cursor-not-allowed disabled:opacity-40 items-center gap-2 rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white hover:bg-[#126a70]"><Sparkles size={17} /> Extract with Gemini</button>
              </div>
            )}
            {demoPhase === "processing" && (
              <div className="mt-6 flex items-center gap-3 rounded-xl bg-[#f2f8f8] p-5 text-sm text-[#173f68]" role="status">
                <LoaderCircle size={22} className="animate-spin text-[#147d83]" /> Analyzing your document with Gemini…
              </div>
            )}
            {demoPhase === "ready" && (
              <form onSubmit={(event) => { event.preventDefault(); applyDemo(); }} className="mt-6 space-y-4">
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">AI suggestions · Accuracy is not guaranteed · Verify every value before applying. Applying replaces the selected document’s current structured fields.</div>
                <div>
                  <label htmlFor="demo-type" className="mb-2 block text-sm font-semibold text-[#173f68]">Suggested document type</label>
                  <select id="demo-type" value={demoDraft.documentType} onChange={(event) => setDemoDraft((previous) => ({ ...previous, documentType: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                    {[...new Set([demoDraft.documentType, ...Object.values(documentTypes).flat()])].map((type) => <option key={type} value={type}>{type}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="demo-name" className="mb-2 block text-sm font-semibold text-[#173f68]">Full name</label>
                  <input id="demo-name" type="text" maxLength={200} value={demoDraft.printedName ?? ""} onChange={(event) => setDemoDraft((previous) => ({ ...previous, printedName: event.target.value }))} className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm" />
                </div>
                <div>
                  <label htmlFor="demo-dob" className="mb-2 block text-sm font-semibold text-[#173f68]">Date of birth</label>
                  <input id="demo-dob" type="date" value={demoDraft.dateOfBirth ?? ""} onChange={(event) => setDemoDraft((previous) => ({ ...previous, dateOfBirth: event.target.value }))} className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm" />
                </div>
                <div>
                  <label htmlFor="demo-address" className="mb-2 block text-sm font-semibold text-[#173f68]">Residential address</label>
                  <textarea id="demo-address" rows={3} maxLength={1000} value={demoDraft.residentialAddress ?? ""} onChange={(event) => setDemoDraft((previous) => ({ ...previous, residentialAddress: event.target.value }))} className="w-full resize-y rounded-xl border border-slate-200 px-4 py-3 text-sm" />
                </div>
                <div className="flex flex-wrap justify-end gap-3 border-t border-slate-100 pt-5">
                  <button type="button" onClick={closeDemo} className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700">Cancel</button>
                  <button type="submit" className="rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white hover:bg-[#126a70]">Review &amp; apply extracted details</button>
                </div>
              </form>
            )}
          </section>
        </div>
      )}

      {editId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-3 sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setEditId(null); }}>
          <section role="dialog" aria-modal="true" aria-labelledby="metadata-dialog-title" className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5 shadow-xl sm:p-7">
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
              <fieldset className="space-y-4 border-t border-slate-100 pt-5">
                <legend className="text-sm font-bold text-[#173f68]">Information printed on document (optional)</legend>
                <p className="text-xs leading-5 text-slate-500">
                  Enter only information that appears on this document. Leave fields blank if absent.
                  This information stays in browser memory for this session and is not verified.
                  Use fictional data while testing.
                </p>
                <div>
                  <label htmlFor="metadata-printed-name" className="mb-2 block text-sm font-semibold text-[#173f68]">Full name as printed</label>
                  <input
                    id="metadata-printed-name"
                    type="text"
                    maxLength={200}
                    autoComplete="off"
                    value={draftMetadata.printedName ?? ""}
                    onChange={(event) => setDraftMetadata((previous) => ({ ...previous, printedName: event.target.value }))}
                    placeholder="e.g. Asha Sharma"
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-[#147d83]"
                  />
                </div>
                <div>
                  <label htmlFor="metadata-dob" className="mb-2 block text-sm font-semibold text-[#173f68]">Date of birth</label>
                  <input
                    id="metadata-dob"
                    type="date"
                    value={draftMetadata.dateOfBirth ?? ""}
                    onChange={(event) => setDraftMetadata((previous) => ({ ...previous, dateOfBirth: event.target.value }))}
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-[#147d83]"
                  />
                </div>
                <div>
                  <label htmlFor="metadata-address" className="mb-2 block text-sm font-semibold text-[#173f68]">Residential address as printed</label>
                  <textarea
                    id="metadata-address"
                    rows={3}
                    maxLength={1000}
                    value={draftMetadata.residentialAddress ?? ""}
                    onChange={(event) => setDraftMetadata((previous) => ({ ...previous, residentialAddress: event.target.value }))}
                    placeholder="Enter the address exactly as shown on this document"
                    className="w-full resize-y rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-[#147d83]"
                  />
                </div>
              </fieldset>
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
