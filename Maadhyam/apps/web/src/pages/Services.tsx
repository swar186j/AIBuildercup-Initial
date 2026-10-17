import PageHero from "../components/PageHero";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, Landmark, Search, Sparkles, Car, HeartPulse, GraduationCap,
  BriefcaseBusiness, Sprout, House, Plug, Scale, Shield, Globe, Monitor,
  Users, BadgeIndianRupee, Building2, Trophy,
} from "lucide-react";
import { filterServiceFamilies, governmentServices, serviceCategories, type ServiceCategory } from "../data/governmentServices";

const PAGE_SIZE = 12;
const categoryIcons = {
  identity: Landmark, family: Users, transport: Car, tax: BadgeIndianRupee,
  housing: House, utilities: Plug, health: HeartPulse, jobs: BriefcaseBusiness,
  welfare: HeartPulse, education: GraduationCap, agriculture: Sprout,
  business: Building2, justice: Scale, tourism: Globe, culture: Trophy,
  digital: Monitor, defence: Shield, governance: Landmark,
};
const scopeLabels = { central: 'Central service', 'state-specific': 'State-specific', varies: 'Availability varies' };

export default function Services() {
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search).get('q') ?? '');
  const [category, setCategory] = useState<ServiceCategory | 'all'>('all');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const filtered = filterServiceFamilies(query, category);
  const visible = filtered.slice(0, visibleCount);
  function resetFilters() {
    setQuery('');
    setCategory('all');
    setVisibleCount(PAGE_SIZE);
  }

  return (
    <div className="pb-24">
      <PageHero eyebrow="Service Navigator" title="Find a government service" description="Explore guided preparation journeys for government services. Passport Seva has an interactive preview; additional services are being developed." />

      <div className="relative mt-8 max-w-xl">
        <Search size={20} aria-hidden="true" className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
        <input type="search" value={query}
          onChange={event => { setQuery(event.target.value); setVisibleCount(PAGE_SIZE); }}
          placeholder="Search passport, Aadhaar, EPFO..." aria-label="Search government services"
          className="w-full rounded-xl border border-slate-200 bg-white py-4 pl-12 pr-4 outline-none focus:border-[#147d83]" />
      </div>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="flex min-w-0 max-w-full flex-col gap-2 text-sm font-semibold text-[#173f68]">
          Category
          <select aria-label="Category" value={category} onChange={event => { setCategory(event.target.value as ServiceCategory | 'all'); setVisibleCount(PAGE_SIZE); }}
            className="max-w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-normal outline-none focus:border-[#147d83] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83]">
            <option value="all">All services</option>
            {serviceCategories.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select>
        </label>
        {(query || category !== 'all') && <button type="button" onClick={resetFilters}
          className="rounded-xl px-4 py-3 text-sm font-semibold text-teal-700 underline focus-visible:outline-2 focus-visible:outline-offset-2">Reset Filters</button>}
      </div>
      <p role="status" aria-live="polite" aria-atomic="true" className="mt-4 text-sm text-slate-600">
        Showing {visible.length} of {filtered.length} service families · {governmentServices.length} catalogue records
      </p>
      <p className="mt-2 text-xs leading-6 text-slate-500">A curated catalogue, not a complete government directory. State-specific services depend on your state or local authority; other availability varies by scheme, provider or jurisdiction. Coming Soon services are not available through Maadhyam.</p>

      <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3" aria-label="Government service catalogue">
        {visible.map(service => {
          const isPassport = service.status === 'guided-preview' && service.supportedRoute === '/services/passport';
          const Icon = categoryIcons[service.category];
          return (
            <article key={service.id} data-service-id={service.id}
              className={`flex min-w-0 flex-col rounded-2xl border bg-white p-7 shadow-sm transition ${isPassport ? 'border-[#c9e1e1] hover:border-[#147d83] hover:shadow-md' : 'border-slate-200'}`}>
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-[#edf5f4] text-[#147d83]">
                <Icon size={23} aria-hidden="true" />
              </div>
              <h2 className="text-xl font-bold text-[#173f68]">{service.title}</h2>
              <p className="mt-3 flex-1 text-sm leading-6 text-slate-600">{service.description}</p>
              <details key={`${service.id}-${query}-${category}`} open={query.trim() ? true : undefined} className="mt-4 text-sm">
                <summary className="cursor-pointer rounded-lg py-2 font-semibold text-[#126a70] focus-visible:outline-2">{service.displayedChildren.length ? `View related services (${service.displayedChildren.length})` : 'Preparation information'}</summary>
                <ul className="mt-2 space-y-3">
                  {service.displayedChildren.map(child=><li key={child.id} data-child-id={child.id} className={`rounded-xl border p-3 ${query.trim() && service.matchingChildren.some(s=>s.id===child.id) ? 'border-teal-600 bg-teal-50' : 'border-slate-200 bg-slate-50'}`}>
                    <h3 className="font-semibold text-[#173f68]">{child.title}</h3>
                    <p className="mt-1 leading-6 text-slate-600">{child.description}</p>
                    <p className="mt-2 text-xs text-slate-500">{scopeLabels[child.scope]} · Guided preparation Coming Soon</p>
                  </li>)}
                </ul>
                {isPassport && <p className="mt-2 leading-6 text-slate-600">New passport, reissue and correction preparation, document review and police verification guidance are available through the Passport preview below. Official applications are completed on the official portal.</p>}
              </details>
              <div className="mt-6 border-t border-slate-100 pt-5">
                {isPassport ? <>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#eaf3f5] px-3 py-1 text-xs font-semibold text-[#126a70]">
                    <Sparkles size={13} aria-hidden="true" />Guided preview available
                  </span>
                  <p className="mt-3 text-xs text-slate-600">New passport · Reissue · Correction · Document preparation · Police verification guidance</p>
                  <Link to="/services/passport" className="mt-5 flex items-center justify-between rounded-xl bg-[#147d83] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#126a70] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83]">
                    Explore Passport Seva<ArrowRight size={18} aria-hidden="true" />
                  </Link>
                </> : <span className="inline-flex rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">Coming Soon</span>}
              </div>
            </article>
          );
        })}
      </div>
      {visible.length < filtered.length && <div className="mt-6 text-center">
        <button type="button" onClick={() => setVisibleCount(count => count + PAGE_SIZE)}
          className="rounded-xl border border-[#147d83] bg-white px-6 py-3 text-sm font-semibold text-[#126a70] hover:bg-[#edf5f4] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83]">Load More</button>
      </div>}
      {filtered.length === 0 && <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 text-center">
        <Search size={28} aria-hidden="true" className="mx-auto text-slate-400" />
        <h2 className="mt-3 font-semibold text-[#173f68]">No matching services found</h2>
        <p className="mt-2 text-sm text-slate-600">Try another search or reset the filters to browse all services.</p>
      </div>}
      <p className="mt-7 text-xs leading-6 text-slate-500">Maadhyam is an independent assistance platform. Guided previews do not confirm eligibility, document acceptance or official application status. Catalogue listings do not imply government affiliation or API integration.</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">Looking for an official service now? <a href="https://services.india.gov.in/feed/index?ln=en" target="_blank" rel="noopener noreferrer" className="font-semibold text-teal-700 underline">Browse the National Government Services Portal (external government website)</a>.</p>
    </div>
  );
}
