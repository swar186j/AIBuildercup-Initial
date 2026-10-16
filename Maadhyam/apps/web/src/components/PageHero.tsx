export default function PageHero({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="relative isolate overflow-hidden rounded-[26px] bg-[#1b4168] px-6 py-10 text-white sm:px-10 sm:py-12">
    <div aria-hidden="true" className="pointer-events-none absolute -right-14 -top-28 h-72 w-72 rounded-full border-[32px] border-[#31567b] opacity-70" />
    <div className="relative z-10 max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-widest text-[#9be8df]">{eyebrow}</p>
      <h1 className="mt-4 text-3xl font-bold leading-tight sm:text-4xl">{title}</h1>
      <p className="mt-4 max-w-2xl text-sm leading-7 text-[#d5e3f1]">{description}</p>
    </div>
  </header>;
}
