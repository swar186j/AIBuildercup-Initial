import { Link } from "react-router-dom";
import {
  ArrowRight,
  FileSearch,
  GitBranch,
  ShieldCheck,
  Sparkles,
  ClipboardCheck,
} from "lucide-react";

const capabilities = [
  {
    title: "Check your documents",
    description:
      "Prepare documents for extraction, review and comparison.",
    icon: FileSearch,
    status: "Coming soon",
  },
  {
    title: "Find correction paths",
    description:
      "Understand dependencies and explore possible corrections.",
    icon: GitBranch,
    status: "Coming soon",
  },
  {
    title: "Understand requirements",
    description:
      "Explore service checklists and verified document rules.",
    icon: ClipboardCheck,
    status: "Coming soon",
  },
];

export default function Dashboard() {
  return (
    <div className="space-y-9">
      <section className="relative overflow-hidden rounded-3xl bg-[#173f68] px-7 py-10 text-white md:px-12 md:py-14">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-xs font-semibold">
            <Sparkles size={15} />
            A simpler path through government services
          </div>

          <h1 className="text-3xl font-bold leading-tight tracking-tight md:text-5xl">
            Your documents.
            <br />
            Your next step.
            <br />
            <span className="text-[#91e0db]">
              Made clearer.
            </span>
          </h1>

          <p className="mt-6 max-w-xl text-sm leading-7 text-blue-100 md:text-base">
            Discover government services and prepare for applications.
            Maadhyam is being built to identify document issues,
            explain verified requirements and help plan corrections.
          </p>

          <Link
            to="/services"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 font-semibold text-[#173f68] transition hover:bg-blue-50"
          >
            Explore services
            <ArrowRight size={18} />
          </Link>
        </div>

        <div className="pointer-events-none absolute -right-24 -top-28 h-96 w-96 rounded-full border-[55px] border-white/5" />
        <div className="pointer-events-none absolute bottom-0 right-12 h-48 w-48 rounded-full bg-[#147d83]/30 blur-3xl" />
      </section>

      <section>
        <div className="mb-6">
          <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">
            What Maadhyam will help you do
          </p>
          <h2 className="mt-2 text-2xl font-bold text-[#173f68]">
            Less confusion. Clearer decisions.
          </h2>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {capabilities.map(({ title, description, icon: Icon, status }) => (
            <article
              key={title}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-[#edf5f4] text-[#147d83]">
                <Icon size={23} />
              </div>

              <h3 className="text-lg font-bold text-[#173f68]">
                {title}
              </h3>

              <p className="mt-3 min-h-16 text-sm leading-6 text-slate-600">
                {description}
              </p>

              <span className="mt-4 inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {status}
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-5 rounded-2xl border border-[#d8e9e7] bg-[#edf5f4] p-6 sm:flex-row sm:items-center">
        <ShieldCheck size={30} className="shrink-0 text-[#147d83]" />

        <div>
          <h3 className="font-semibold text-[#173f68]">
            Designed for trustworthy guidance
          </h3>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Our planned rules engine will distinguish verified government
            requirements from AI-generated explanations. Maadhyam is
            independent and does not submit applications to government
            departments.
          </p>
        </div>
      </section>
    </div>
  );
}