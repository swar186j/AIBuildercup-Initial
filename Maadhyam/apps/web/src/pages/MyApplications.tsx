import PreparationJourneyProgress from '../components/PreparationJourneyProgress';
import { formatDateTime } from "../utils/dateTime";
import { useDialogFocus } from '../hooks/useDialogFocus';
import PreparationStorageControls from '../components/PreparationStorageControls';
import PageHero from "../components/PageHero";

import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, CheckCircle2, ClipboardList,
  Clock3, FileText, Plus, Search, X,
  GitBranch, UploadCloud
} from "lucide-react";
import { useWorkspace, type Status } from "../context/WorkspaceContext";

const statusText: Record<Status, string> = {
  draft: "Not started",
  "in-progress": "Preparing",
  completed: "Preparation completed"
};

const statusStyle: Record<Status, string> = {
  draft: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-100",
  "in-progress": "bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
  completed: "bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
};

type Filter = "all" | Status;

const card =
  "rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-[#293956] dark:bg-[#18243B]";
const heading = "text-[#173f68] dark:text-slate-100";
const muted = "text-slate-600 dark:text-slate-400";
const accent = "text-[#147d83] dark:text-[#2FE9C2]";

export default function MyApplications() {
  const { applications, createDraft: createWorkspaceDraft, deletePreparation } = useWorkspace();

  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [notice, setNotice] = useState("");

  useDialogFocus(!!selectedId,'[aria-labelledby="application-detail-title"]',()=>setSelectedId(null));
  const selected = applications.find(app => app.id === selectedId);

  const filtered = useMemo(
    () =>
      applications.filter(
        app =>
          (filter === "all" || app.status === filter) &&
          `${app.service} ${app.type} ${app.id} ${app.journey?.applicantName ?? ""}`
            .toLowerCase()
            .includes(query.trim().toLowerCase())
      ),
    [applications, filter, query]
  );

  const creating=useRef(false);
  useEffect(()=>{if(!selectedId)creating.current=false;},[selectedId]);
  function createDraft() {
    if(creating.current)return;
    creating.current=true;
    const id = createWorkspaceDraft();
    setFilter("all");
    setQuery("");
    setNotice(
      "New preparation draft created in this browser session. This is not a government application."
    );
    setSelectedId(id);
  }

  return (
    <div className="w-full space-y-7 pb-24">
      <PageHero eyebrow="Your preparation workspace" title="My Preparations" description="Keep track of your preparation records, review pending steps and continue where you left off." />
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1 rounded-xl border border-[#cde5e3] bg-[#f2f8f8] px-4 py-3 text-sm leading-6 text-[#173f68] dark:border-[#293956] dark:bg-[#18243B] dark:text-slate-200">
          <strong>Preparation only:</strong> These are Maadhyam preparation records, not government applications or official status updates. Session-only changes disappear when you refresh unless you explicitly enable preparation saving below.
        </div>
        <button
          type="button"
          disabled={!!selectedId}
          onClick={createDraft}
          className="inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-xl bg-[#147d83] px-5 py-3 text-sm font-semibold text-white hover:bg-[#126a70] lg:self-auto"
        >
          <Plus size={18} />
          Start new preparation
        </button>
      </div>

      <PreparationJourneyProgress/>
      <p className="text-sm text-slate-600 dark:text-slate-300">Questionnaire completion is separate from evidence readiness. Resume a saved preparation to see its current applicable document checklist and outstanding review tasks. Maadhyam does not track official government application status.</p>
      <PreparationStorageControls />
      {notice && (
        <p role="status" className={`text-sm ${accent}`}>
          {notice}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          {
            label: "All preparations",
            count: applications.length,
            icon: ClipboardList
          },
          {
            label: "Currently preparing",
            count: applications.filter(
              app => app.status === "in-progress"
            ).length,
            icon: Clock3
          },
          {
            label: "Preparation completed",
            count: applications.filter(
              app => app.status === "completed"
            ).length,
            icon: CheckCircle2
          }
        ].map(({ label, count, icon: Icon }) => (
          <div key={label} className={card}>
            <div className={`flex items-center justify-between text-sm font-medium ${muted}`}>
              <span>{label}</span>
              <Icon size={20} className={accent} />
            </div>

            <p className={`mt-4 text-3xl font-bold ${heading}`}>
              {count}
            </p>
          </div>
        ))}
      </div>

      <section className={card}>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <h2 className={`text-lg font-bold ${heading}`}>
            Your preparation records
          </h2>

          <div className="relative w-full lg:max-w-xs">
            <Search
              size={17}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              aria-label="Search preparations"
              value={query}
              onChange={event => setQuery(event.target.value)}
              placeholder="Search preparations..."
              className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm text-slate-900 outline-none focus:border-[#147d83] dark:border-[#304653] dark:bg-[#203440] dark:text-slate-100"
            />
          </div>
        </div>

        <div
          className="mt-5 flex flex-wrap gap-2"
          aria-label="Filter preparations"
        >
          {(["all", "draft", "in-progress", "completed"] as Filter[]).map(
            value => (
              <button
                key={value}
                type="button"
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
                className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                  filter === value
                    ? "bg-[#147d83] text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-[#203440] dark:text-slate-300"
                }`}
              >
                {value === "all" ? "All" : statusText[value]}
              </button>
            )
          )}
        </div>

        <div className="mt-6 space-y-4">
          {filtered.length === 0 && (
            <p className={`rounded-xl bg-slate-50 p-8 text-center text-sm dark:bg-[#203440] ${muted}`}>
              No matching preparation records.
            </p>
          )}

          {filtered.map(app => {
            const progress = app.totalSteps
              ? Math.min(
                  100,
                  Math.max(
                    0,
                    Math.round(
                      (app.completedSteps / app.totalSteps) * 100
                    )
                  )
                )
              : 0;

            return (
              <article
                key={app.id}
                className="rounded-2xl border border-slate-200 p-5 dark:border-[#304653]"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="flex min-w-0 gap-3">
                    <div className="h-fit rounded-xl bg-[#edf5f4] p-3 text-[#147d83] dark:bg-[#203440] dark:text-[#2FE9C2]">
                      <FileText size={22} />
                    </div>

                    <div className="min-w-0">
                      <p className={`text-xs font-semibold ${muted}`}>
                        {app.id} · {app.updated}
                      </p>

                      <h3 className={`mt-1 text-base font-bold ${heading}`}>
                        {app.type}
                      </h3>

                      <p className={`mt-1 text-sm ${muted}`}>
                        {app.service} · Preparation only
                      </p>
                      <p className={`mt-1 text-xs ${muted}`}>Created on: <time dateTime={app.createdAt}>{formatDateTime(app.createdAt)}</time></p>
                      <p className={`text-xs ${muted}`}>Last saved: <time dateTime={app.lastSavedAt}>{formatDateTime(app.lastSavedAt)}</time></p>
                      <p className={`text-xs ${muted}`}>Current step: {app.journey?`Step ${app.journey.stepIndex+1} of ${app.totalSteps}`:'Not recorded'}</p>
                      {app.journey?.applicantName && (
                        <p className={`mt-1 text-sm ${muted}`}>
                          Applicant: {app.journey.applicantName}
                        </p>
                      )}
                    </div>
                  </div>

                  <span
                    className={`w-fit rounded-full px-3 py-1.5 text-xs font-semibold ${statusStyle[app.status]}`}
                  >
                    {statusText[app.status]}
                  </span>
                </div>

                <div className={`mt-5 flex items-center justify-between text-xs ${muted}`}>
                  <span>Demo preparation checklist</span>
                  <span>
                    {app.completedSteps} of {app.totalSteps} steps · {progress}%
                  </span>
                </div>

                <div
                  className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-[#203440]"
                  role="progressbar"
                  aria-valuenow={progress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${app.type} preparation progress`}
                >
                  <div
                    className="h-full rounded-full bg-[#147d83] dark:bg-[#2FE9C2]"
                    style={{ width: `${progress}%` }}
                  />
                </div>

                <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className={`text-sm ${muted}`}>
                    <span className={`font-semibold ${heading}`}>
                      Next:
                    </span>{" "}
                    {app.nextAction}
                  </p>

                  <button
                    type="button"
                    onClick={() => setSelectedId(app.id)}
                    className={`inline-flex shrink-0 items-center gap-2 text-sm font-semibold hover:underline ${accent}`}
                  >
                    {app.status === "completed"
                      ? "View preparation summary"
                      : "Continue preparation"}
                    <ArrowRight size={16} />
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-3 sm:p-6"
          role="presentation"
          onMouseDown={event => {
            if (event.target === event.currentTarget) {
              setSelectedId(null);
            }
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="application-detail-title"
            className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl dark:bg-[#18243B] sm:p-7"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className={`text-xs font-semibold ${muted}`}>
                  {selected.id}
                </p>

                <h2
                  id="application-detail-title"
                  className={`mt-1 text-xl font-bold ${heading}`}
                >
                  {selected.type}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setSelectedId(null)}
                aria-label="Close preparation details"
                className={`rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-[#203440] ${muted}`}
              >
                <X size={20} />
              </button>
            </div>

            <p className={`mt-3 text-sm leading-6 ${muted}`}>
              Your local preparation checklist. This does not
              represent a government application or official
              verification.
            </p>

            <ol className="mt-6 space-y-3">
              {selected.steps.map((step, index) => (
                <li
                  key={`${index}-${step}`}
                  className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-sm dark:border-[#304653]"
                >
                  {index < selected.completedSteps ? (
                    <CheckCircle2
                      size={20}
                      className={`shrink-0 ${accent}`}
                    />
                  ) : (
                    <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-300 text-xs dark:border-slate-600 ${muted}`}>
                      {index + 1}
                    </span>
                  )}

                  <span
                    className={
                      index < selected.completedSteps
                        ? muted
                        : `font-medium ${heading}`
                    }
                  >
                    {step}
                  </span>
                </li>
              ))}
            </ol>

            {selected.journey&&<button type="button" onClick={()=>{deletePreparation(selected.id);setSelectedId(null);}} className="mt-4 text-sm text-red-700 underline">Delete this preparation</button>}
            <p className="mt-3 text-xs">Created on: {formatDateTime(selected.createdAt)} · Last saved: {formatDateTime(selected.lastSavedAt)}</p>
            <p className="mt-3 text-sm">Remaining questionnaire steps: {Math.max(0,selected.totalSteps-selected.completedSteps)}. Evidence readiness may still need review after the questionnaire is complete.</p>
            <a href="https://www.passportindia.gov.in/" target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm text-teal-700 underline">Verify next steps on the official Passport Seva portal</a>
            <button type="button" className="ml-3 text-sm text-teal-700 underline" onClick={()=>{setSelectedId(null);window.dispatchEvent(new Event('maadhyam-open-assistant'));}}>Ask Maadhyam AI</button>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <Link
                to={selected.journey?`/services/passport/journey?type=${selected.journey.assistanceType}&preparation=${encodeURIComponent(selected.id)}`:"/services/passport/journey"}
                onClick={() => setSelectedId(null)}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#147d83] px-4 py-3 text-sm font-semibold text-white hover:bg-[#126a70]"
              >
                {selected.status === "completed"
                  ? "View saved questionnaire"
                  : "Continue passport journey"}
                <ArrowRight size={16} />
              </Link>

              <Link
                to="/planner"
                onClick={() => setSelectedId(null)}
                className={`inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold dark:border-[#304653] ${accent}`}
              >
                <GitBranch size={16} />
                Review preparation plan
              </Link>

              <Link
                to="/documents"
                onClick={() => setSelectedId(null)}
                className={`inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold dark:border-[#304653] ${heading}`}
              >
                <UploadCloud size={16} />
                Review documents
              </Link>

              <Link
                to="/services"
                onClick={() => setSelectedId(null)}
                className={`inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold dark:border-[#304653] ${heading}`}
              >
                Explore services
                <ArrowRight size={16} />
              </Link>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
