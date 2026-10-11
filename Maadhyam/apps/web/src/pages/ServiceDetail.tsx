
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  FilePlus2,
  RefreshCw,
  FilePenLine,
  Files,
  ShieldCheck,
  Landmark,
  Info,
} from "lucide-react";
import {
  passportAssistanceOptions,
  passportOfficialUrl,
  passportJourneyDisclaimer,
  type PassportAssistanceType,
} from "../data/journeyData";

const assistanceIcons = {
  fresh: FilePlus2,
  reissue: RefreshCw,
  correction: FilePenLine,
  documents: Files,
  police: ShieldCheck,
};

export default function ServiceDetail() {
  const { serviceId } = useParams();

  if (serviceId !== "passport") {
    return (
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8">
        <h1 className="text-2xl font-bold text-[#173f68]">
          Guided journey coming soon
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          This service does not have a guided preparation
          experience yet.
        </p>
        <Link
          to="/services"
          className="mt-6 inline-flex items-center gap-2 font-semibold text-[#147d83]"
        >
          <ArrowLeft size={17} />
          Back to services
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      {/* Breadcrumb */}
      <Link
        to="/services"
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-[#147d83]"
      >
        <ArrowLeft size={17} />
        All Services
      </Link>

      {/* Service hero */}
      <section className="rounded-3xl bg-[#173f68] p-7 text-white md:p-10">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white/15">
            <Landmark size={28} />
          </div>

          <div>
            <span className="inline-block rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
              Guided Preparation
            </span>

            <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
              Passport Seva
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-200 md:text-base">
              Understand your situation, review available
              documents and identify areas that may need
              attention before proceeding through official
              Passport Seva channels.
            </p>
          </div>
        </div>
      </section>

      {/* Assistance options */}
      <section>
        <div className="mb-5">
          <h2 className="text-2xl font-bold text-[#173f68]">
            What do you need help with?
          </h2>

          <p className="mt-2 text-sm text-slate-600">
            Choose an assistance journey to get started.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {passportAssistanceOptions.map((option) => {
            const Icon =
              assistanceIcons[
                option.id as PassportAssistanceType
              ];

            return (
              <Link
                key={option.id}
                to={`/services/passport/journey?type=${option.id}`}
                className="group flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-[#147d83] hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83]"
              >
                <div>
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#eaf3f5] text-[#147d83]">
                    <Icon size={23} />
                  </div>

                  <h3 className="text-base font-bold text-[#173f68]">
                    {option.label}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {option.description}
                  </p>
                </div>

                <div className="mt-6 flex items-center gap-2 text-sm font-semibold text-[#147d83]">
                  Start guided journey
                  <ArrowRight
                    size={17}
                    className="transition-transform group-hover:translate-x-1"
                  />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Transparency notice */}
      <section className="rounded-2xl border border-[#d5e7e6] bg-[#f0f7f6] p-5">
        <div className="flex items-start gap-3">
          <Info
            size={20}
            className="mt-0.5 shrink-0 text-[#147d83]"
          />

          <div>
            <h2 className="text-sm font-bold text-[#173f68]">
              Independent guidance, official verification
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              {passportJourneyDisclaimer}
            </p>

            <a
              href={passportOfficialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[#126a70] underline underline-offset-4"
            >
              Visit official Passport Seva website
              <ExternalLink size={15} />
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
