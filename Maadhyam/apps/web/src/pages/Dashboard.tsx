import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, ClipboardList, FileSearch, Files, GitBranch, Landmark, ShieldCheck, Sparkles, UploadCloud, AlertTriangle, Clock3 } from "lucide-react";
import { useDocuments } from "../context/DocumentContext";
import { useWorkspace, plannerTasks } from "../context/WorkspaceContext";
import { compareDocuments } from "../utils/documentComparison";

export default function Dashboard() {
  const { documents } = useDocuments();
  const { applications, plannerCompleted } = useWorkspace();
  const reviewed = documents.filter((doc) => doc.status === "reviewed").length;
  const incomplete = documents.filter((doc) => !doc.metadata.printedName?.trim() || !doc.metadata.dateOfBirth || !doc.metadata.residentialAddress?.trim()).length;
  const findings = compareDocuments(documents).findings;
  const active = applications.filter((app) => app.status !== "completed").length;
  const nextTask = plannerTasks.find((task) => !plannerCompleted.includes(task.id) && task.dependsOn.every((id) => plannerCompleted.includes(id)));
  const progress = Math.round(plannerCompleted.length / plannerTasks.length * 100);
  const recentDocuments = [...documents].sort((a,b) => b.addedAt.getTime() - a.addedAt.getTime()).slice(0,3);
  const stats = [
    { label: "Documents in Vault", value: documents.length, note: `${reviewed} self-reviewed`, icon: Files, href: "/documents" },
    { label: "Active preparations", value: active, note: "Includes fictional demo records", icon: ClipboardList, href: "/applications" },
    { label: "Planner progress", value: `${progress}%`, note: `${plannerCompleted.length} of ${plannerTasks.length} steps`, icon: GitBranch, href: "/planner" },
    { label: "Possible differences", value: findings.length, note: "Based on entered metadata", icon: FileSearch, href: "/documents" },
  ];
  return (
    <div className="space-y-7 pb-24">
      <section className="relative overflow-hidden rounded-3xl bg-[#173f68] px-6 py-9 text-white sm:px-10 sm:py-11">
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-2 text-xs font-semibold"><Sparkles size={15}/> Your citizen workspace · Frontend demo</span>
          <h1 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">Your documents. Your next step. <span className="text-[#91e0db]">Made clearer.</span></h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-blue-100">Explore services, organize sample documents and track preparation progress in one place. Nothing here represents an official application status.</p>
          <Link to="/services" className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#173f68] hover:bg-blue-50">Explore services <ArrowRight size={17}/></Link>
        </div>
        <div className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full border-[42px] border-white/5"/>
      </section>

      <section aria-label="Workspace overview" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ label,value,note,icon:Icon,href }) => <Link key={label} to={href} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-[#8cc5c3] hover:shadow-md">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-600">{label}</p><Icon size={20} className="text-[#147d83]"/></div>
          <p className="mt-3 text-3xl font-bold text-[#173f68]">{value}</p><p className="mt-2 text-xs text-slate-500">{note}</p>
          <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#147d83]">Open workspace <ArrowRight size={13}/></span>
        </Link>)}
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center gap-2"><GitBranch size={20} className="text-[#147d83]"/><h2 className="text-lg font-bold text-[#173f68]">Your next preparation step</h2></div>
          <p className="mt-2 text-sm text-slate-600">{nextTask?.title ?? "All demo planner steps completed."}</p>
          <div className="mt-5 flex justify-between text-xs text-slate-600"><span>Planner completion</span><strong>{progress}%</strong></div>
          <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-label="Planner completion" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><div className="h-full rounded-full bg-[#147d83]" style={{width:`${progress}%`}}/></div>
          <Link to="/planner" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#147d83] hover:underline">Open Resolution Planner <ArrowRight size={16}/></Link>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center gap-2"><FileSearch size={20} className="text-[#147d83]"/><h2 className="text-lg font-bold text-[#173f68]">Document intelligence</h2></div>
          {documents.length === 0 ? <p className="mt-3 text-sm leading-6 text-slate-600">No documents yet. Upload fictional sample documents to see metadata readiness and possible differences.</p> : <div className="mt-4 space-y-3 text-sm"><p className="flex items-center gap-2 text-slate-700"><AlertTriangle size={17} className="text-amber-600"/> {findings.length} potential field differences</p><p className="flex items-center gap-2 text-slate-700"><Clock3 size={17} className="text-[#147d83]"/> {incomplete} documents with missing structured fields</p><p className="flex items-center gap-2 text-slate-700"><CheckCircle2 size={17} className="text-[#147d83]"/> {reviewed} files marked self-reviewed</p></div>}
          <p className="mt-3 text-xs leading-5 text-slate-500">Findings are advisory comparisons of entered or demo metadata, not document verification.</p>
          <Link to="/documents" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[#147d83] hover:underline">Open Document Vault <ArrowRight size={16}/></Link>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-bold text-[#173f68]">Quick actions</h2>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            {title:"Upload documents",description:"Organize sample files",href:"/documents",icon:UploadCloud},
            {title:"Find services",description:"Explore supported services",href:"/services",icon:Landmark},
            {title:"Passport journey",description:"Review guided preparation",href:"/services/passport/journey",icon:ClipboardList},
            {title:"My applications",description:"Manage demo preparation records",href:"/applications",icon:Files},
          ].map(({title,description,href,icon:Icon}) => <Link key={title} to={href} className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 hover:border-[#8cc5c3] hover:bg-[#f4faf9]"><span className="rounded-xl bg-[#edf5f4] p-3 text-[#147d83]"><Icon size={20}/></span><span className="min-w-0"><strong className="block text-sm text-[#173f68]">{title}</strong><span className="text-xs text-slate-500">{description}</span></span><ArrowRight size={16} className="ml-auto shrink-0 text-slate-400"/></Link>)}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex items-center justify-between gap-3"><h2 className="text-lg font-bold text-[#173f68]">Recent document activity</h2><Link to="/documents" className="text-sm font-semibold text-[#147d83] hover:underline">View all</Link></div>
        {recentDocuments.length === 0 ? <p className="mt-4 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">No activity yet. Your latest uploaded sample files will appear here.</p> : <ul className="mt-4 divide-y divide-slate-100">{recentDocuments.map((doc)=><li key={doc.id} className="flex items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="truncate text-sm font-semibold text-[#173f68]">{doc.file.name}</p><p className="text-xs text-slate-500">Added {doc.addedAt.toLocaleString()}</p></div><span className="shrink-0 text-xs text-slate-500">{doc.status === "reviewed" ? "Self-reviewed" : "Needs review"}</span></li>)}</ul>}
      </section>
      <div className="flex items-start gap-3 rounded-xl border border-[#d8e9e7] bg-[#edf5f4] p-4 text-xs leading-6 text-slate-600"><ShieldCheck size={20} className="mt-0.5 shrink-0 text-[#147d83]"/><p>Maadhyam is an independent assistance platform. Application records and planner progress are frontend-only demos. No government application is submitted, and no document is officially verified.</p></div>
    </div>
  );
}
