import { useEffect, useState } from "react";
import { assessPassport, type PassportAssessment } from "../services/passportAssessment";
import {
  Link,
  useSearchParams,
} from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronLeft,
  ExternalLink,
  Info,
  ShieldCheck,
  FolderOpen,
} from "lucide-react";
import {
  initialPassportAnswers,
  passportAssistanceOptions,
  passportJourneyDisclaimer,
  passportJourneySteps,
  passportOfficialUrl,
  type PassportAssistanceType,
  type PassportJourneyAnswers,
} from "../data/journeyData";
import { useDocuments, getDocumentCategories, type DocumentCategory } from "../context/DocumentContext";
type GuidancePriority = "attention" | "review" | "information";
type GuidanceItem = {
  id: string;
  title: string;
  priority: GuidancePriority;
  concern: string;
  check: string;
  action: string;
};
function generatePreparationGuidance(
  answers: PassportJourneyAnswers,
): GuidanceItem[] {
  const guidance: GuidanceItem[] = [];
  if (answers.applicantAgeGroup === "minor") {
    guidance.push({
      id: "minor",
      title: "Minor applicant considerations",
      priority: "information",
      concern:
        "Passport preparation for a minor may involve additional applicant and parent or guardian considerations.",
      check:
        "Review the current official instructions for minor applicants, including applicable parent or guardian documentation and consent requirements.",
      action:
        "Check the official Passport Seva guidance for your specific minor application situation.",
    });
  }
  if (answers.currentAddressMatches === "no") {
    guidance.push({
      id: "address-mismatch",
      title: "Residential address discrepancy",
      priority: "attention",
      concern:
        "You indicated that your residential address does not match the relevant document or application record.",
      check:
        "Compare the complete address, including house details, locality, city and PIN code, across your records.",
      action:
        "Review the applicable official address-document instructions before proceeding.",
    });
  } else if (answers.currentAddressMatches === "unsure") {
    guidance.push({
      id: "address-uncertain",
      title: "Address consistency needs review",
      priority: "review",
      concern:
        "You are unsure whether your address information is consistent.",
      check:
        "Compare your current residential address with the address shown on the relevant document or application.",
      action:
        "Confirm the discrepancy, if any, before relying on the document.",
    });
  }
  if (answers.nameConsistent === "no") {
    guidance.push({
      id: "name-mismatch",
      title: "Name discrepancy across documents",
      priority: "attention",
      concern:
        "You indicated that your name is not consistent across your available documents.",
      check:
        "Compare spelling, name order, initials and other differences across the records.",
      action:
        "Review official guidance on the evidence or correction process applicable to your circumstances.",
    });
  } else if (answers.nameConsistent === "unsure") {
    guidance.push({
      id: "name-uncertain",
      title: "Name consistency needs confirmation",
      priority: "review",
      concern:
        "You are unsure whether your name is consistent across your documents.",
      check:
        "Compare the name displayed on each available document.",
      action:
        "Identify any differences and review the relevant official instructions.",
    });
  }
  const documentChecks = [
    {
      key: "hasIdentityDocument",
      title: "Identity document availability",
      description: "an identity document",
    },
    {
      key: "hasAddressDocument",
      title: "Address document availability",
      description: "a current-address document",
    },
    {
      key: "hasDateOfBirthDocument",
      title: "Date of birth document availability",
      description: "a date-of-birth document",
    },
  ] as const;
  for (const document of documentChecks) {
    const answer = answers[document.key];
    if (answer === "no" || answer === "unsure") {
      guidance.push({
        id: document.key,
        title: document.title,
        priority: answer === "no" ? "attention" : "review",
        concern:
          answer === "no"
            ? `You indicated that you do not currently have ${document.description} available.`
            : `You are unsure whether you have ${document.description} available.`,
        check:
          "Review the current official document instructions for your application category. Different documents may be accepted in different circumstances.",
        action:
          "Identify which officially accepted evidence you can provide. Do not assume a specific document is mandatory.",
      });
    }
  }
  if (answers.policeVerificationStatus === "delayed") {
    guidance.push({
      id: "police-delay",
      title: "Police verification delay",
      priority: "attention",
      concern:
        "You reported that police verification appears delayed.",
      check:
        "Check the latest status using the official Passport Seva tracking facility and review any instructions already issued.",
      action:
        "If the delay persists, use the appropriate official Passport Seva enquiry or grievance channel.",
    });
  }
  if (answers.policeVerificationStatus === "adverse") {
    guidance.push({
      id: "police-adverse",
      title: "Adverse or unclear verification report",
      priority: "attention",
      concern:
        "You reported an adverse or unclear police verification outcome.",
      check:
        "Review any official communication to understand the reported issue. Avoid assuming the cause from the status alone.",
      action:
        "Seek clarification through the relevant official Passport Seva or Regional Passport Office channel.",
    });
  }
  if (
    answers.policeVerificationStatus === "unknown" ||
    answers.policeVerificationStatus === "pending"
  ) {
    guidance.push({
      id: "police-status",
      title: "Police verification status follow-up",
      priority: "review",
      concern:
        "Your verification status may require confirmation or monitoring.",
      check:
        "Check the latest available status through official tracking channels.",
      action:
        "Follow the instructions associated with your specific application.",
    });
  }
  const priorityOrder: Record<GuidancePriority, number> = {
    attention: 0,
    review: 1,
    information: 2,
  };
  return guidance.sort(
    (a, b) =>
      priorityOrder[a.priority] - priorityOrder[b.priority],
  );
}
type AnswerKey = keyof PassportJourneyAnswers;
type Question = {
  key: AnswerKey;
  label: string;
  options: {
    value: string;
    label: string;
  }[];
};
const yesNoUnsure = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
  { value: "unsure", label: "I'm not sure" },
];
const questionsByType: Record<
  PassportAssistanceType,
  { context: Question[]; documents: Question[] }
> = {
  fresh: {
    context: [
      {
        key: "applicantAgeGroup",
        label: "Who is the passport application for?",
        options: [
          { value: "adult", label: "An adult" },
          { value: "minor", label: "A minor" },
        ],
      },
      {
        key: "currentAddressMatches",
        label:
          "Does your current residential address match your available address document?",
        options: yesNoUnsure,
      },
    ],
    documents: [
      {
        key: "hasIdentityDocument",
        label: "Do you have an identity document available?",
        options: yesNoUnsure,
      },
      {
        key: "hasAddressDocument",
        label: "Do you have a document showing your current address?",
        options: yesNoUnsure,
      },
      {
        key: "hasDateOfBirthDocument",
        label: "Do you have a document showing your date of birth?",
        options: yesNoUnsure,
      },
      {
        key: "nameConsistent",
        label: "Is your name consistent across your documents?",
        options: yesNoUnsure,
      },
    ],
  },
  reissue: {
    context: [
      {
        key: "applicantAgeGroup",
        label: "Who needs the passport reissue?",
        options: [
          { value: "adult", label: "An adult" },
          { value: "minor", label: "A minor" },
        ],
      },
      {
        key: "currentAddressMatches",
        label: "Does your current address match your available records?",
        options: yesNoUnsure,
      },
    ],
    documents: [
      {
        key: "hasIdentityDocument",
        label: "Do you have an identity document available?",
        options: yesNoUnsure,
      },
      {
        key: "hasAddressDocument",
        label: "Do you have a document showing your current address?",
        options: yesNoUnsure,
      },
      {
        key: "nameConsistent",
        label: "Are your personal details consistent across records?",
        options: yesNoUnsure,
      },
    ],
  },
  correction: {
    context: [
      {
        key: "nameConsistent",
        label: "Do your existing documents show the same name?",
        options: yesNoUnsure,
      },
      {
        key: "currentAddressMatches",
        label: "Do your documents show your current residential address?",
        options: yesNoUnsure,
      },
    ],
    documents: [
      {
        key: "hasIdentityDocument",
        label: "Do you have an identity document available?",
        options: yesNoUnsure,
      },
      {
        key: "hasAddressDocument",
        label: "Do you have an address document available?",
        options: yesNoUnsure,
      },
    ],
  },
  documents: {
    context: [
      {
        key: "applicantAgeGroup",
        label: "Whose documents are you preparing?",
        options: [
          { value: "adult", label: "An adult" },
          { value: "minor", label: "A minor" },
        ],
      },
    ],
    documents: [
      {
        key: "hasIdentityDocument",
        label: "Do you have an identity document available?",
        options: yesNoUnsure,
      },
      {
        key: "hasAddressDocument",
        label: "Do you have an address document available?",
        options: yesNoUnsure,
      },
      {
        key: "hasDateOfBirthDocument",
        label: "Do you have a date of birth document available?",
        options: yesNoUnsure,
      },
      {
        key: "nameConsistent",
        label: "Are names consistent across your documents?",
        options: yesNoUnsure,
      },
    ],
  },
  police: {
    context: [
      {
        key: "policeVerificationStatus",
        label: "What is your current police verification situation?",
        options: [
          { value: "not-started", label: "Not started" },
          { value: "pending", label: "Verification pending" },
          { value: "completed", label: "Verification completed" },
          { value: "delayed", label: "Facing a delay" },
          { value: "adverse", label: "Adverse or unclear report" },
          { value: "unknown", label: "I don't know the status" },
        ],
      },
      {
        key: "currentAddressMatches",
        label:
          "Does your current residential address match the address provided in your application?",
        options: yesNoUnsure,
      },
    ],
    documents: [
      {
        key: "hasAddressDocument",
        label: "Do you have a document showing your current address?",
        options: yesNoUnsure,
      },
      {
        key: "hasIdentityDocument",
        label: "Do you have an identity document available?",
        options: yesNoUnsure,
      },
    ],
  },
};
function QuestionField({
  question,
  value,
  onChange,
}: {
  question: Question;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <fieldset className="space-y-3">
      <legend className="mb-3 text-sm font-semibold text-[#173f68]">
        {question.label}
      </legend>
      <div className="grid gap-3 sm:grid-cols-2">
        {question.options.map((option) => (
          <label
            key={option.value}
            className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 text-sm transition ${value === option.value
                ? "border-[#147d83] bg-[#eaf3f5] text-[#126a70]"
                : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
              }`}
          >
            <input
              type="radio"
              name={question.key}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="accent-[#147d83]"
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
export default function GuidedJourney() {
  const [searchParams] = useSearchParams();
  const requestedType = searchParams.get("type");
  const validType = passportAssistanceOptions.find(
    (option) => option.id === requestedType,
  );
  const assistanceType: PassportAssistanceType =
    validType?.id ?? "fresh";
  return (
    <PassportWizard
      key={assistanceType}
      assistanceType={assistanceType}
    />
  );
}
function PassportWizard({
  assistanceType,
}: {
  assistanceType: PassportAssistanceType;
}) {
  const { documents } = useDocuments();
  const [stepIndex, setStepIndex] = useState(0);
  const [answers, setAnswers] = useState<PassportJourneyAnswers>({
    ...initialPassportAnswers,
    assistanceType,
  });
  const [showValidation, setShowValidation] = useState(false);
  const [assessment, setAssessment] = useState<PassportAssessment | null>(null);
  const [assessmentError, setAssessmentError] = useState('');
  const [applicantDob, setApplicantDob] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    const handle = window.setTimeout(() => {
      assessPassport(answers as unknown as Record<string, unknown>, documents, applicantDob, controller.signal)
        .then(result => { if (!controller.signal.aborted) { setAssessment(result); setAssessmentError(''); } })
        .catch(error => { if (!controller.signal.aborted) setAssessmentError(error instanceof Error ? error.message : 'Assessment unavailable'); });
    }, 300);
    return () => { window.clearTimeout(handle); controller.abort(); };
  }, [answers, documents, applicantDob]);
  const option = passportAssistanceOptions.find(
    (item) => item.id === assistanceType,
  );
  const step = passportJourneySteps[stepIndex];
  const progress = ((stepIndex + 1) / passportJourneySteps.length) * 100;
  const currentQuestions =
    step.id === "context"
      ? questionsByType[assistanceType].context
      : step.id === "documents"
        ? questionsByType[assistanceType].documents
        : [];
  const unanswered = currentQuestions.filter(
    (question) => !answers[question.key],
  );
  function updateAnswer(key: AnswerKey, value: string) {
    setAnswers((previous) => ({
      ...previous,
      [key]: value,
    }));
    setShowValidation(false);
  }
  function goNext() {
    if (unanswered.length > 0) {
      setShowValidation(true);
      return;
    }
    setShowValidation(false);
    setStepIndex((previous) =>
      Math.min(previous + 1, passportJourneySteps.length - 1),
    );
  }
  function goBack() {
    setShowValidation(false);
    setStepIndex((previous) => Math.max(previous - 1, 0));
  }
  const answerLabels: Record<string, string> = {
    yes: "Yes",
    no: "No",
    unsure: "Not sure",
    adult: "Adult",
    minor: "Minor",
    "not-started": "Not started",
    pending: "Pending",
    completed: "Completed",
    delayed: "Delayed",
    adverse: "Adverse or unclear report",
    unknown: "Unknown",
  };
  const allQuestions = [
    ...questionsByType[assistanceType].context,
    ...questionsByType[assistanceType].documents,
  ];
  const guidanceItems = generatePreparationGuidance(answers);
  const attentionCount = guidanceItems.filter(
    (item) => item.priority === "attention",
  ).length;
  const reviewCount = guidanceItems.filter(
    (item) => item.priority === "review",
  ).length;
  const informationCount = guidanceItems.filter(
    (item) => item.priority === "information",
  ).length;
  const hasConcerns = attentionCount > 0 || reviewCount > 0;
  const documentChecks: {
    key: "hasIdentityDocument" | "hasAddressDocument" | "hasDateOfBirthDocument";
    label: string;
    category: DocumentCategory;
  }[] = [
    { key: "hasIdentityDocument", label: "Identity proof", category: "identity" },
    { key: "hasAddressDocument", label: "Address proof", category: "address" },
    { key: "hasDateOfBirthDocument", label: "Date of birth", category: "birth" },
  ];

  // Compare only categories actually asked in this assistance journey.
  const vaultChecks = documentChecks
    .filter((item) => allQuestions.some((question) => question.key === item.key))
    .map((item) => ({
      ...item,
      count: documents.filter((document) => getDocumentCategories(document.metadata).includes(item.category)).length,
      response: answers[item.key],
    }));

  // Vault gaps are organizational reminders, not eligibility or acceptance findings.
  const vaultGaps = vaultChecks.filter(
    (item) => item.response === "yes" && item.count === 0,
  );
  const vaultAnswerMismatches = vaultChecks.filter(
    (item) => item.response === "no" && item.count > 0,
  );
  const hasVaultFollowUps = vaultGaps.length > 0 || vaultAnswerMismatches.length > 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Link
        to="/services/passport"
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-[#147d83]"
      >
        <ArrowLeft size={17} />
        Back to Passport Seva
      </Link>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 text-slate-900 dark:border-[#293956] dark:bg-[#18243B] dark:text-slate-100 shadow-sm md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-teal-700 dark:text-[#96B1FF]">Passport preparation</p>
            <h2 className="mt-1 text-lg font-bold">Tell us about your application</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Answer the questions below. Your official-source checklist is shown after the questionnaire.</p>
          </div>
          <a className="text-xs font-semibold text-teal-700 dark:text-[#96B1FF] underline underline-offset-4" href="https://www.passportindia.gov.in/psp/docAdvisor/attachmentAdvFreshInp" target="_blank" rel="noreferrer">Passport Seva Document Advisor ↗</a>
        </div>
        <label className="mt-4 block text-sm font-semibold" htmlFor="applicant-dob">Applicant date of birth</label>
        <input id="applicant-dob" type="date" value={applicantDob} onChange={event => setApplicantDob(event.target.value)} className="mt-2 w-full max-w-xs rounded-lg border border-slate-300 bg-white p-3 text-sm text-slate-900 [color-scheme:light] dark:border-slate-600 dark:bg-[#101A30] dark:text-white dark:[color-scheme:dark]" />
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Required to select the official date-of-birth evidence rule (1 October 2023 cutoff).</p>
      </section>
      <section className="rounded-3xl bg-gradient-to-r from-[#124b50] to-[#173f68] p-7 text-white md:p-9">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
          <ShieldCheck size={15} />
          Guided Preparation
        </div>
        <h1 className="text-2xl font-bold md:text-3xl">
          {option?.label}
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-200">
          Answer a few questions to organize your preparation.
          This is not an official eligibility assessment.
        </p>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-[#147d83]">
              Step {stepIndex + 1} of {passportJourneySteps.length}
            </p>
            <h2 className="mt-2 text-xl font-bold text-[#173f68]">
              {step.title}
            </h2>
          </div>
          <span className="text-sm font-semibold text-slate-500">
            {Math.round(progress)}%
          </span>
        </div>
        <div
          role="progressbar"
          aria-label="Journey progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
          className="mb-8 h-2 overflow-hidden rounded-full bg-slate-100"
        >
          <div
            className="h-full rounded-full bg-[#147d83] transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mb-7 text-sm text-slate-600">
          {step.description}
        </p>
        {/* Step 1: Assistance */}
        {step.id === "assistance" && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-[#173f68]">
              What do you need help with?
            </h3>
            <div className="space-y-3">
              {passportAssistanceOptions.map((item) => (
                <Link
                  key={item.id}
                  to={`/services/passport/journey?type=${item.id}`}
                  className={`flex items-center justify-between gap-4 rounded-xl border p-4 transition ${assistanceType === item.id
                      ? "border-[#147d83] bg-[#eaf3f5]"
                      : "border-slate-200 hover:border-slate-300"
                    }`}
                >
                  <div>
                    <p className="text-sm font-semibold text-[#173f68]">
                      {item.label}
                    </p>
                    <p className="mt-1 text-xs text-slate-600">
                      {item.description}
                    </p>
                  </div>
                  {assistanceType === item.id ? (
                    <CheckCircle2
                      size={21}
                      className="shrink-0 text-[#147d83]"
                    />
                  ) : (
                    <ArrowRight
                      size={18}
                      className="shrink-0 text-slate-400"
                    />
                  )}
                </Link>
              ))}
            </div>
          </div>
        )}
        {/* Steps 2 and 3: Questions */}
        {(step.id === "context" || step.id === "documents") && (
          <div className="space-y-8">
            {currentQuestions.map((question) => (
              <QuestionField
                key={question.key}
                question={question}
                value={answers[question.key]}
                onChange={(value) =>
                  updateAnswer(question.key, value)
                }
              />
            ))}
            {showValidation && unanswered.length > 0 && (
              <p
                role="alert"
                className="rounded-xl bg-amber-50 p-4 text-sm font-medium text-amber-800"
              >
                Please answer all questions before continuing.
                You can select "I'm not sure" where available.
              </p>
            )}
          </div>
        )}
        {/* Step 4: Summary */}
        {step.id === "summary" && (
          <div className="space-y-6">
            <div className="rounded-xl bg-[#edf5f4] p-5">
              <div className="flex items-center gap-2 text-[#126a70]">
                <CheckCircle2 size={20} />
                <h3 className="font-bold">
                  Preparation questionnaire completed
                </h3>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Your responses have been collected in this
                browser session. No official application has
                been submitted.
              </p>
            </div>
            <div>
              <h3 className="mb-4 text-lg font-bold text-[#173f68]">
                Your responses
              </h3>
              <div className="space-y-3">
                {allQuestions.map((question) => (
                  <div
                    key={question.key}
                    className="rounded-xl border border-slate-200 p-4"
                  >
                    <p className="text-sm text-slate-600">
                      {question.label}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-[#173f68]">
                      {answerLabels[answers[question.key]] ??
                        "Not provided"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            {/* Concise overview replaces duplicate areas-to-review list */}
          <section className="space-y-4">
            <h3 className="text-lg font-bold text-[#173f68]">
              Preparation overview
            </h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                <p className="text-2xl font-bold text-amber-900">{attentionCount}</p>
                <p className="mt-2 text-sm font-medium text-amber-800">Needs attention</p>
              </div>
              <div className="rounded-xl border border-sky-200 bg-sky-50 p-5">
                <p className="text-2xl font-bold text-sky-900">{reviewCount}</p>
                <p className="mt-2 text-sm font-medium text-sky-800">Review suggested</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                <p className="text-2xl font-bold text-slate-900">{informationCount}</p>
                <p className="mt-2 text-sm font-medium text-slate-600">Information</p>
              </div>
            </div>
            <p className="text-xs leading-6 text-slate-500">
              These counts reflect questionnaire-based suggestions, not verified
              document defects or eligibility decisions.
            </p>
          </section>

          {/* Document Vault comparison — file presence is not document validation */}
          <section className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="flex items-center gap-2 text-lg font-bold text-[#173f68]">
                  <FolderOpen size={20} className="text-[#147d83]" />
                  Document Vault readiness
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Compare your answers with files manually categorized in Maadhyam.
                  A file not appearing here does not mean you do not own that document.
                </p>
              </div>
              <Link
                to="/documents"
                className="inline-flex items-center gap-2 rounded-xl bg-[#147d83] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#126a70]"
              >
                Manage documents <ArrowRight size={16} />
              </Link>
            </div>

            {vaultChecks.length > 0 ? (
              <div className="space-y-3">
                {vaultChecks.map((item) => (
                  <div
                    key={item.category}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4"
                  >
                    <div>
                      <p className="text-sm font-semibold text-[#173f68]">{item.label}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Questionnaire answer: {answerLabels[item.response] ?? "Not provided"}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-semibold ${
                        item.count > 0 ? "text-[#126a70]" : "text-slate-600"
                      }`}>
                        {item.count > 0
                          ? `${item.count} categorized ${item.count === 1 ? "file" : "files"} in Vault`
                          : "No categorized file in Vault"}
                      </p>
                      {item.response === "yes" && item.count === 0 && (
                        <p className="mt-1 text-xs text-amber-700">
                          You said Yes, but no matching file is stored here.
                        </p>
                      )}
                      {item.response === "no" && item.count > 0 && (
                        <p className="mt-1 text-xs text-sky-700">
                          Your answer and Vault contents may need reconciliation.
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600">
                This journey did not ask document availability questions.
              </p>
            )}
            <p className="text-xs leading-5 text-slate-500">
              Categories are manually assigned. Maadhyam has not inspected or verified these
              files, checked whether they belong to the applicant, or confirmed acceptance
              under Passport Seva rules. A document may support multiple purposes.
            </p>
          </section>

          {/* Show detailed guidance only when a rule is triggered */}
          {guidanceItems.length > 0 && (
            <section className="space-y-4">
              <div>
                <h3 className="text-lg font-bold text-[#173f68]">
                  Personalized preparation guidance
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Suggestions based on your responses, not official eligibility
                  or document acceptance decisions.
                </p>
              </div>
              <div className="space-y-4">
                {guidanceItems.map((item) => (
                  <article
                    key={item.id}
                    className={`rounded-2xl border p-5 ${
                      item.priority === "attention"
                        ? "border-amber-200 bg-amber-50"
                        : item.priority === "review"
                          ? "border-sky-200 bg-sky-50"
                          : "border-slate-200 bg-slate-50"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <h4 className="font-bold text-[#173f68]">{item.title}</h4>
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          item.priority === "attention"
                            ? "bg-amber-100 text-amber-800"
                            : item.priority === "review"
                              ? "bg-sky-100 text-sky-800"
                              : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        {item.priority === "attention"
                          ? "Needs attention"
                          : item.priority === "review"
                            ? "Review suggested"
                            : "Information"}
                      </span>
                    </div>
                    <div className="mt-4 space-y-4 text-sm leading-6 text-slate-700">
                      <div>
                        <p className="font-semibold text-[#173f68]">What's the concern?</p>
                        <p className="mt-1">{item.concern}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-[#173f68]">What should you check?</p>
                        <p className="mt-1">{item.check}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-[#173f68]">Suggested next action</p>
                        <p className="mt-1">{item.action}</p>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          <div className="rounded-xl border border-slate-200 p-5">
              <h3 className="font-bold text-[#173f68]">
                Suggested next steps
              </h3>
                          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-600">
              {hasConcerns && (
                <li>
                  Review the questionnaire concerns highlighted above before
                  proceeding with preparation.
                </li>
              )}
              {vaultGaps.length > 0 && (
                <li>
                  You indicated that you have {vaultGaps.map((item) => item.label.toLowerCase()).join(", ")},
                  but no file is currently categorized under {vaultGaps.length === 1 ? "that category" : "those categories"}
                  in your Document Vault. You can add or classify files there if you wish;
                  this is not proof that your documents are missing.
                </li>
              )}
              {vaultAnswerMismatches.length > 0 && (
                <li>
                  Review the difference between your questionnaire answers and
                  the Vault categories for {vaultAnswerMismatches.map((item) => item.label.toLowerCase()).join(", ")}.
                  Categorization is manual and may not reflect the actual documents available to you.
                </li>
              )}
              {!hasConcerns && !hasVaultFollowUps && (
                <li>
                  No questionnaire concerns or Vault comparison follow-ups were
                  identified. This does not confirm eligibility or document acceptance.
                </li>
              )}
              <li>
                Verify the latest official Passport Seva instructions for
                your application category.
              </li>
              <li>
                Continue through the appropriate official application or
                enquiry channel when ready.
              </li>
            </ol>
              <a
                href={passportOfficialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-5 inline-flex items-center gap-2 font-semibold text-[#126a70] underline underline-offset-4"
              >
                Official Passport Seva website
                <ExternalLink size={16} />
              </a>
            </div>
          </div>
        )}
        {/* Navigation */}
        <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-6 pb-16 sm:pb-20">
          <button
            type="button"
            onClick={goBack}
            disabled={stepIndex === 0}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronLeft size={17} />
            Back
          </button>
          {step.id !== "summary" ? (
            <button
              type="button"
              onClick={goNext}
              className="inline-flex items-center gap-2 rounded-xl bg-[#147d83] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#126a70]"
            >
              Continue
              <ArrowRight size={17} />
            </button>
          ) : (
            <Link
              to="/services/passport"
              className="inline-flex items-center gap-2 rounded-xl bg-[#147d83] px-6 py-3 text-sm font-semibold text-white hover:bg-[#126a70]"
            >
              Finish
              <CheckCircle2 size={17} />
            </Link>
          )}
        </div>
      </section>
      <section aria-label="Passport document requirements" className="rounded-2xl border border-slate-200 bg-white p-5 text-slate-900 dark:border-[#293956] dark:bg-[#18243B] dark:text-slate-100 shadow-sm md:p-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-teal-700 dark:text-[#96B1FF]">Your document plan</p>
            <h2 className="mt-1 text-xl font-bold">Official-source requirements</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Based on your answers and self-reviewed Document Vault records. Not an approval decision.</p>
          </div>
          <a href="https://www.passportindia.gov.in/psp/docAdvisor/attachmentAdvFreshInp" target="_blank" rel="noreferrer" className="text-xs font-semibold text-teal-700 dark:text-[#96B1FF] underline underline-offset-4">Verify with Passport Seva ↗</a>
        </div>
        {assessmentError && <p role="alert" className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">Unable to load the checklist: {assessmentError}. Check that the API is running.</p>}
        {!assessment && !assessmentError && <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">Updating your checklist…</p>}
        {assessment && <>
          <div className="mt-5 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-slate-100 px-3 py-1.5 text-slate-700 dark:bg-slate-700/70 dark:text-slate-100">{assessment.checks.length} requirements to review</span>
            <span className="rounded-full bg-teal-50 px-3 py-1.5 text-teal-800 dark:bg-teal-500/10 dark:text-[#96B1FF]">{assessment.checks.filter(c => c.status === 'available-for-review').length} possible proofs found</span>
            <span className="rounded-full bg-amber-50 px-3 py-1.5 text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">{assessment.checks.filter(c => c.status !== 'available-for-review').length} need follow-up</span>
          </div>
          {assessment.source_health !== 'current' && <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">Official-source monitoring needs review ({assessment.source_health}). These are preparation suggestions, not confirmation that government rules are unchanged. Verify your case using the official links.</p>}
          {assessment.checks.length === 0 ? <p className="mt-5 text-sm text-slate-600 dark:text-slate-400">No requirements returned for these answers. Confirm your case using the official Document Advisor.</p> :
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {assessment.checks.map((check, i) => <article key={check.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-[#293956] dark:bg-[#101A30] md:p-5">
              <div className="flex items-start gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-100 text-xs font-bold text-teal-800 dark:bg-teal-500/10 dark:text-[#96B1FF]">{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold leading-6">{check.title}</h3>
                  <span className={`mt-1 inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium ${check.status === 'available-for-review' ? 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-[#96B1FF]' : check.status === 'needs-attention' ? 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-200' : 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-200'}`}>{check.status === 'available-for-review' ? 'Proof to review' : check.status === 'needs-attention' ? 'Action needed' : 'Check required'}</span>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-300">{check.reason}</p>
              <p className="mt-3 text-sm leading-6"><strong className="text-teal-800 dark:text-[#96B1FF]">What to do:</strong> {check.next_action}</p>
              {check.alternatives.length > 0 && <details className="mt-3 rounded-lg bg-white p-3 text-xs text-slate-700 dark:bg-[#202F4A] dark:text-slate-300"><summary className="cursor-pointer font-semibold text-teal-800 dark:text-[#96B1FF]">See possible supporting documents</summary><p className="mt-2 leading-5">{check.alternatives.join(' · ')}. Conditions and applicant category restrictions apply.</p></details>}
              {check.source_url && <a href={check.source_url} target="_blank" rel="noreferrer" className="mt-4 inline-block text-xs font-semibold text-teal-700 dark:text-[#96B1FF] underline underline-offset-4">View government source ↗</a>}
            </article>)}
          </div>}
          <p className="mt-5 text-xs leading-5 text-slate-500 dark:text-slate-400">{assessment.disclaimer}</p>
        </>}
      </section>
      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-5">
        <Info
          size={19}
          className="mt-0.5 shrink-0 text-[#147d83]"
        />
        <p className="text-xs leading-6 text-slate-600">
          {passportJourneyDisclaimer}
        </p>
      </div>
    </div>
  );
}
