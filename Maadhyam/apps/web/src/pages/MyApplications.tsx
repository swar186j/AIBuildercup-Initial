import { useMemo, useState } from "react";
import { useWorkspace, type Status } from "../context/WorkspaceContext";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, ClipboardList, Clock3, FileText, Plus, Search, X } from "lucide-react";

const statusText: Record<Status, string> = { draft: "Draft", "in-progress": "In progress", completed: "Completed" };
const statusStyle: Record<Status, string> = {
  draft: "bg-slate-100 text-slate-700",
  "in-progress": "bg-amber-50 text-amber-800",
  completed: "bg-emerald-50 text-emerald-800",
};

type Filter = "all" | Status;

export default function MyApplications() {
  const { applications, createDraft: createWorkspaceDraft, backendState } = useWorkspace();
  const [creating, setCreating] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const selected = applications.find((app) => app.id === selectedId);
  const filtered = useMemo(() => applications.filter((app) =>
    (filter === "all" || app.status === filter) &&
    `${app.service} ${app.type} ${app.id}`.toLowerCase().includes(query.trim().toLowerCase()),
  ), [applications, filter, query]);

  async function createDraft() {
    if (creating) return;
    setCreating(true);
    const { id, savedToBackend } = await createWorkspaceDraft();
    setCreating(false);
    setFilter("all");
    setQuery("");
    setNotice(savedToBackend ? "Demo draft saved to the local FastAPI database. Not a government application." : "Backend unavailable: demo draft saved only in this browser. Not a government application.");
    setSelectedId(id);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-7 pb-24">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">Application workspace</p>
          <h1 className="mt-2 text-3xl font-bold text-[#173f68]">My Applications</h1>
          <p className="mt-3 max-w-2xl leading-7 text-slate-600">Track preparation progress, pending tasks and next steps in one place.</p>
        </div>
        <button type="button" onClick={createDraft} disabled={creating} className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white hover:bg-[#126a70]">
          <Plus size={18} /> {creating ? "Creating…" : "New demo draft"}
        </button>
      </header>

      <div className="rounded-xl border border-[#cde5e3] bg-[#f2f8f8] px-4 py-3 text-sm leading-6 text-[#173f68]">
        <strong>Demo workspace:</strong> Fictional preparation records only, not submitted applications or official status updates. Browser records survive refresh. Backend connection: {backendState === "connected" ? "connected (new drafts saved to local API)" : backendState === "loading" ? "checking…" : "offline (new drafts stay in this browser)"}. Existing browser-only drafts are not automatically uploaded.
      </div>
      {notice && <p role="status" className="text-sm text-[#147d83]">{notice}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        {([
          { label: "All applications", count: applications.length, icon: ClipboardList },
          { label: "In progress", count: applications.filter((app) => app.status === "in-progress").length, icon: Clock3 },
          { label: "Completed", count: applications.filter((app) => app.status === "completed").length, icon: CheckCircle2 },
        ]).map(({ label, count, icon: Icon }) => (
          <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between text-sm font-medium text-slate-600"><span>{label}</span><Icon size={20} className="text-[#147d83]" /></div>
            <p className="mt-4 text-3xl font-bold text-[#173f68]">{count}</p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <h2 className="text-lg font-bold text-[#173f68]">Preparation records</h2>
          <div className="relative w-full lg:max-w-xs">
            <Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input aria-label="Search applications" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search applications..." className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-3 text-sm outline-none focus:border-[#147d83]" />
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2" aria-label="Filter applications">
          {(["all", "draft", "in-progress", "completed"] as Filter[]).map((value) => (
            <button key={value} type="button" aria-pressed={filter === value} onClick={() => setFilter(value)} className={`rounded-full px-4 py-2 text-xs font-semibold ${filter === value ? "bg-[#147d83] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
              {value === "all" ? "All" : statusText[value]}
            </button>
          ))}
        </div>
        <div className="mt-6 space-y-4">
          {filtered.length === 0 && <p className="rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-600">No matching preparation records.</p>}
          {filtered.map((app) => {
            const progress = Math.round((app.completedSteps / app.totalSteps) * 100);
            return (
              <article key={app.id} className="rounded-2xl border border-slate-200 p-5">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="flex min-w-0 gap-3">
                    <div className="h-fit rounded-xl bg-[#edf5f4] p-3 text-[#147d83]"><FileText size={22} /></div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-500">{app.id} · {app.updated}</p>
                      <h3 className="mt-1 text-base font-bold text-[#173f68]">{app.type}</h3>
                      <p className="mt-1 text-sm text-slate-600">{app.service} · Preparation only</p>
                    </div>
                  </div>
                  <span className={`w-fit rounded-full px-3 py-1.5 text-xs font-semibold ${statusStyle[app.status]}`}>{statusText[app.status]}</span>
                </div>
                <div className="mt-5 flex items-center justify-between text-xs text-slate-600"><span>Preparation progress</span><span>{app.completedSteps} of {app.totalSteps} steps · {progress}%</span></div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label={`${app.type} progress`}>
                  <div className="h-full rounded-full bg-[#147d83]" style={{ width: `${progress}%` }} />
                </div>
                <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-slate-600"><span className="font-semibold text-[#173f68]">Next:</span> {app.nextAction}</p>
                  <button type="button" onClick={() => setSelectedId(app.id)} className="inline-flex shrink-0 items-center gap-2 text-sm font-semibold text-[#147d83] hover:underline">View details <ArrowRight size={16} /></button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-3 sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedId(null); }}>
          <section role="dialog" aria-modal="true" aria-labelledby="application-detail-title" className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl sm:p-7">
            <div className="flex items-start justify-between gap-3">
              <div><p className="text-xs font-semibold text-slate-500">{selected.id}</p><h2 id="application-detail-title" className="mt-1 text-xl font-bold text-[#173f68]">{selected.type}</h2></div>
              <button type="button" onClick={() => setSelectedId(null)} aria-label="Close application details" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"><X size={20} /></button>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">Demo preparation checklist. Progress is illustrative and is not connected to the Passport Seva portal.</p>
            <ol className="mt-6 space-y-3">
              {selected.steps.map((step, index) => (
                <li key={step} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-sm">
                  {index < selected.completedSteps ? <CheckCircle2 size={20} className="shrink-0 text-[#147d83]" /> : <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-300 text-xs text-slate-500">{index + 1}</span>}
                  <span className={index < selected.completedSteps ? "text-slate-600" : "font-medium text-[#173f68]"}>{step}</span>
                </li>
              ))}
            </ol>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/services/passport/journey" onClick={() => setSelectedId(null)} className="inline-flex items-center gap-2 rounded-xl bg-[#147d83] px-4 py-3 text-sm font-semibold text-white hover:bg-[#126a70]">Open passport journey <ArrowRight size={16} /></Link>
              <Link to="/documents" onClick={() => setSelectedId(null)} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-[#173f68] hover:bg-slate-50">Open Document Vault</Link>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
