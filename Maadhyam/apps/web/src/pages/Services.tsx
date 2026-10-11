
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Landmark,
  Search,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  fetchServices,
  type GovernmentService,
} from "../services/api";

export default function Services() {
  const [services, setServices] = useState<GovernmentService[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadServices() {
    setLoading(true);
    setError("");

    try {
      setServices(await fetchServices());
    } catch {
      setError(
        "Unable to load services. Please check the backend connection.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadServices();
  }, []);

  const filtered = services.filter((service) =>
    `${service.name} ${service.description}`
      .toLowerCase()
      .includes(query.trim().toLowerCase()),
  );

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">
        Service Navigator
      </p>

      <h1 className="mt-2 text-3xl font-bold text-[#173f68]">
        Find a government service
      </h1>

      <p className="mt-3 max-w-2xl leading-7 text-slate-600">
        Explore guided preparation journeys for government
        services. Passport Seva has an interactive preview;
        additional services are being developed.
      </p>

      {/* Search */}
      <div className="relative mt-8 max-w-xl">
        <Search
          size={20}
          className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
        />

        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search passport, Aadhaar, EPFO..."
          aria-label="Search government services"
          className="w-full rounded-xl border border-slate-200 bg-white py-4 pl-12 pr-4 outline-none focus:border-[#147d83]"
        />
      </div>

      {/* Loading */}
      {loading && (
        <p role="status" className="mt-8 text-slate-600">
          Loading services...
        </p>
      )}

      {/* Error */}
      {error && (
        <div
          role="alert"
          className="mt-8 rounded-xl border border-red-200 bg-red-50 p-5 text-red-700"
        >
          <p>{error}</p>

          <button
            type="button"
            onClick={() => void loadServices()}
            className="mt-3 inline-flex items-center gap-2 font-semibold underline"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      )}

      {/* Service cards */}
      {!loading && !error && (
        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((service) => {
            const isPassport = service.id === "passport";

            return (
              <article
                key={service.id}
                className={`flex flex-col rounded-2xl border bg-white p-7 shadow-sm transition ${
                  isPassport
                    ? "border-[#c9e1e1] hover:border-[#147d83] hover:shadow-md"
                    : "border-slate-200"
                }`}
              >
                <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-[#edf5f4] text-[#147d83]">
                  <Landmark size={23} />
                </div>

                <h2 className="text-xl font-bold text-[#173f68]">
                  {service.name}
                </h2>

                <p className="mt-3 min-h-16 flex-1 text-sm leading-6 text-slate-600">
                  {service.description}
                </p>

                <div className="mt-6 border-t border-slate-100 pt-5">
                  {isPassport ? (
                    <>
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-[#eaf3f5] px-3 py-1 text-xs font-semibold text-[#126a70]">
                        <Sparkles size={13} />
                        Guided preview available
                      </span>

                      <Link
                        to="/services/passport"
                        className="mt-5 flex items-center justify-between rounded-xl bg-[#147d83] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#126a70] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83]"
                      >
                        Explore Passport Seva
                        <ArrowRight size={18} />
                      </Link>
                    </>
                  ) : (
                    <span className="inline-flex rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                      {service.status === "planned"
                        ? "Coming soon"
                        : service.status}
                    </span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filtered.length === 0 && (
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 text-center">
          <Search
            size={28}
            className="mx-auto text-slate-400"
          />

          <h2 className="mt-3 font-semibold text-[#173f68]">
            No matching services found
          </h2>

          <p className="mt-2 text-sm text-slate-600">
            Try searching for Passport, Aadhaar or EPFO.
          </p>
        </div>
      )}

      {/* Transparency */}
      {!loading && !error && (
        <p className="mt-7 text-xs leading-6 text-slate-500">
          Maadhyam is an independent assistance platform.
          Guided previews do not confirm eligibility,
          document acceptance or official application status.
        </p>
      )}
    </div>
  );
}
