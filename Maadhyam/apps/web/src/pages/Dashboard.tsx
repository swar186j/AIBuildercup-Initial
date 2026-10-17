import PreparationJourneyProgress from '../components/PreparationJourneyProgress';
import {useHousehold} from '../context/HouseholdContext';

import { Link } from "react-router-dom";
import {
  ArrowRight, CheckCircle2, ClipboardList, FileSearch,
  Files, GitBranch, Landmark, ShieldCheck, Sparkles,
  UploadCloud, AlertTriangle, Clock3
} from "lucide-react";
import { useDocuments } from "../context/DocumentContext";
import { useWorkspace, plannerTasks } from "../context/WorkspaceContext";
import { compareDocuments } from "../utils/documentComparison";

const card = "rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-[#293956] dark:bg-[#18243B]";
const heading = "text-[#173f68] dark:text-slate-100";
const muted = "text-slate-600 dark:text-slate-400";
const accent = "text-[#147d83] dark:text-[#2FE9C2]";

export default function Dashboard() {
  const {members}=useHousehold();
  const { documents } = useDocuments();
  const { applications, plannerCompleted } = useWorkspace();

  const reviewed = documents.filter(
    doc => doc.status === "reviewed" && doc.metadata.holder === "self"
  ).length;

  const incomplete = documents.filter(
    doc =>
      !doc.metadata.printedName?.trim() ||
      !doc.metadata.dateOfBirth ||
      !doc.metadata.residentialAddress?.trim()
  ).length;

  const comparison=compareDocuments(documents,new Set(members.map(m=>m.id)));
  const findings=comparison.comparisons.filter(c=>c.status==='difference'&&!c.needsReview);
  const resume=applications.find(a=>a.journey&&a.status!=='completed')??applications.find(a=>a.journey);
  const active = applications.filter(app => app.journey && app.status !== "completed").length;

  const completedIds = new Set(plannerCompleted);
  const completedCount = plannerTasks.filter(task => completedIds.has(task.id)).length;

  const nextTask = plannerTasks.find(
    task =>
      !completedIds.has(task.id) &&
      task.dependsOn.every(id => completedIds.has(id))
  );

  const progress = plannerTasks.length
    ? Math.round((completedCount / plannerTasks.length) * 100)
    : 0;

  const recentDocuments = [...documents]
    .sort((a, b) => b.addedAt.getTime() - a.addedAt.getTime())
    .slice(0, 3);

  const stats = [
    {
      label: "Documents in Vault",
      value: documents.length,
      note: `${reviewed} reviewed self-held`,
      icon: Files,
      href: "/documents"
    },
    {
      label: "Active preparations",
      value: active,
      note: "Your session, local and cloud preparations",
      icon: ClipboardList,
      href: "/applications"
    },
    {
      label: "Demo checklist progress",
      value: `${progress}%`,
      note: `${completedCount} of ${plannerTasks.length} steps`,
      icon: GitBranch,
      href: "/planner"
    },
    {
      label: "Possible differences",
      value: findings.length,
      note: "Reviewed same-person field pairs",
      icon: FileSearch,
      href: "/planner"
    }
  ];

  return (
    <div className="space-y-7 pb-24">
      <section className="relative overflow-hidden rounded-3xl bg-[#173f68] px-6 py-9 text-white sm:px-10 sm:py-11">
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-2 text-xs font-semibold">
            <Sparkles size={15} />
            Your citizen workspace
          </span>

          <h1 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">
            Your documents. Your next step.{" "}
            <span className="text-[#91e0db]">Made clearer.</span>
          </h1>

          <p className="mt-4 max-w-xl text-sm leading-7 text-blue-100">
            Organize your sample documents, understand potential
            discrepancies and prepare for government services
            through one connected journey.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to={resume?`/services/passport/journey?preparation=${encodeURIComponent(resume.id)}`:"/services/passport/journey"}
              className="inline-flex items-center gap-2 rounded-xl bg-[#2FE9C2] px-5 py-3 text-sm font-bold text-[#123044] transition hover:bg-[#7CF5DC]"
            >
              {resume?'Resume your preparation':'Start passport preparation'}
              <ArrowRight size={17} />
            </Link>

            <Link
              to="/services"
              className="inline-flex items-center gap-2 rounded-xl border border-white/30 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/10"
            >
              Explore services
            </Link>
          </div>
        </div>

        <div className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full border-[42px] border-white/5" />
      </section>

      <section className={card} aria-label="Discover supported services"><h2 className={`font-bold ${heading}`}>Find your service</h2><form action="/services" method="get" className="mt-3 flex flex-wrap gap-3"><input type="search" name="q" aria-label="Search services from landing" placeholder="Passport, Aadhaar, EPFO…" className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white p-3 text-slate-900"/><button className="rounded-xl bg-[#147d83] px-4 py-3 font-semibold text-white">Find services</button></form><p className={`mt-3 text-sm ${muted}`}>Passport: guided preparation · Aadhaar and EPFO: advisory service information.</p><div className={`mt-3 flex flex-wrap gap-4 text-sm ${accent}`}><Link to="/services/passport" className="underline">Passport assistance</Link><Link to="/services?q=Aadhaar" className="underline">Aadhaar guidance</Link><Link to="/services?q=EPFO" className="underline">EPFO guidance</Link></div></section>
      <PreparationJourneyProgress/>
      <section
        aria-label="Workspace overview"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        {stats.map(({ label, value, note, icon: Icon, href }) => (
          <Link
            key={label}
            to={href}
            className={`${card} group transition hover:border-[#8cc5c3] hover:shadow-md`}
          >
            <div className="flex items-center justify-between">
              <p className={`text-sm font-medium ${muted}`}>{label}</p>
              <Icon size={20} className={accent} />
            </div>

            <p className={`mt-3 text-3xl font-bold ${heading}`}>
              {value}
            </p>
            <p className={`mt-2 text-xs ${muted}`}>{note}</p>

            <span className={`mt-3 inline-flex items-center gap-1 text-xs font-semibold ${accent}`}>
              View details <ArrowRight size={13} />
            </span>
          </Link>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className={card}>
          <div className="flex items-center gap-2">
            <GitBranch size={20} className={accent} />
            <h2 className={`text-lg font-bold ${heading}`}>
              Your next preparation step
            </h2>
          </div>

          <p className={`mt-3 text-sm ${muted}`}>
            {nextTask?.title ??
              (plannerTasks.length === completedCount
                ? "All demo checklist steps completed."
                : "Review your preparation plan for next steps.")}
          </p>

          <div className={`mt-5 flex justify-between text-xs ${muted}`}>
            <span>Demo checklist completion</span>
            <strong>{progress}%</strong>
          </div>

          <div
            className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-100 dark:bg-[#203440]"
            role="progressbar"
            aria-label="Demo checklist completion"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="h-full rounded-full bg-[#147d83] dark:bg-[#2FE9C2]"
              style={{ width: `${progress}%` }}
            />
          </div>

          <p className={`mt-2 text-xs ${muted}`}>
            This is locally tracked demo progress, not government
            application progress or an eligibility decision.
          </p>

          <Link
            to="/planner"
            className={`mt-5 inline-flex items-center gap-2 text-sm font-semibold hover:underline ${accent}`}
          >
            Open Resolution Planner <ArrowRight size={16} />
          </Link>
        </div>

        <div className={card}>
          <div className="flex items-center gap-2">
            <FileSearch size={20} className={accent} />
            <h2 className={`text-lg font-bold ${heading}`}>
              Document intelligence
            </h2>
          </div>

          {documents.length === 0 ? (
            <p className={`mt-3 text-sm leading-6 ${muted}`}>
              No documents yet. Upload fictional sample documents
              to review metadata and detect possible differences.
            </p>
          ) : (
            <div className="mt-4 space-y-3 text-sm">
              <p className={`flex items-center gap-2 ${muted}`}>
                <AlertTriangle size={17} className="text-amber-600" />
                {findings.length} potential field differences
              </p>

              <p className={`flex items-center gap-2 ${muted}`}>
                <Clock3 size={17} className={accent} />
                {incomplete} documents with missing structured fields
              </p>

              <p className={`flex items-center gap-2 ${muted}`}>
                <CheckCircle2 size={17} className={accent} />
                {reviewed} reviewed self-held documents
              </p>
            </div>
          )}

          <p className={`mt-3 text-xs leading-5 ${muted}`}>
            Findings are advisory comparisons of entered metadata,
            not official document verification.
          </p>

          <Link
            to="/documents"
            className={`mt-4 inline-flex items-center gap-2 text-sm font-semibold hover:underline ${accent}`}
          >
            Open Document Vault <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <section>
        <h2 className={`mb-4 text-xl font-bold ${heading}`}>
          Your preparation journey
        </h2>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            {
              title: "1. Review documents",
              description: "Upload and review sample records",
              href: "/documents",
              icon: UploadCloud
            },
            {
              title: "2. Prepare for Passport",
              description: "Follow guided preparation",
              href: "/services/passport/journey",
              icon: Landmark
            },
            {
              title: "3. Resolve differences",
              description: "Explore corrections and scenarios",
              href: "/planner",
              icon: GitBranch
            },
            {
              title: "4. Track preparation",
              description: "View your local preparation records",
              href: "/applications",
              icon: ClipboardList
            }
          ].map(({ title, description, href, icon: Icon }) => (
            <Link
              key={title}
              to={href}
              className={`${card} flex items-center gap-3 transition hover:border-[#8cc5c3]`}
            >
              <span className="rounded-xl bg-[#edf5f4] p-3 text-[#147d83] dark:bg-[#203440] dark:text-[#2FE9C2]">
                <Icon size={20} />
              </span>

              <span className="min-w-0 flex-1">
                <strong className={`block text-sm ${heading}`}>
                  {title}
                </strong>
                <span className={`text-xs ${muted}`}>
                  {description}
                </span>
              </span>

              <ArrowRight
                size={16}
                className="shrink-0 text-slate-400"
              />
            </Link>
          ))}
        </div>
      </section>

      <section className={card}>
        <div className="flex items-center justify-between gap-3">
          <h2 className={`text-lg font-bold ${heading}`}>
            Recent document activity
          </h2>

          <Link
            to="/documents"
            className={`text-sm font-semibold hover:underline ${accent}`}
          >
            View all
          </Link>
        </div>

        {recentDocuments.length === 0 ? (
          <p className={`mt-4 rounded-xl bg-slate-50 p-5 text-sm dark:bg-[#203440] ${muted}`}>
            No activity yet. Your latest uploaded sample files
            will appear here.
          </p>
        ) : (
          <ul className="mt-4 divide-y divide-slate-100 dark:divide-[#293956]">
            {recentDocuments.map(doc => (
              <li
                key={doc.id}
                className="flex items-center justify-between gap-3 py-3"
              >
                <div className="min-w-0">
                  <p className={`truncate text-sm font-semibold ${heading}`}>
                    {doc.file.name}
                  </p>
                  <p className={`text-xs ${muted}`}>
                    Added {doc.addedAt.toLocaleString()}
                  </p>
                </div>

                <span className={`shrink-0 text-xs ${muted}`}>
                  {doc.status === "reviewed"
                    ? "Manually reviewed"
                    : "Needs review"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="flex items-start gap-3 rounded-xl border border-[#d8e9e7] bg-[#edf5f4] p-4 text-xs leading-6 text-slate-600 dark:border-[#293956] dark:bg-[#18243B] dark:text-slate-400">
        <ShieldCheck
          size={20}
          className="mt-0.5 shrink-0 text-[#147d83] dark:text-[#2FE9C2]"
        />
        <p>
          Maadhyam is an independent assistance platform.
          Preparation records use session, optional local saving or acknowledged cloud saving. No government application is submitted,
          and no document is officially verified.
        </p>
      </div>
    </div>
  );
}
