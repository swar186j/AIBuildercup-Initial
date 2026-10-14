
import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Services from "./pages/Services";
import ServiceDetail from "./pages/ServiceDetail";
import GuidedJourney from "./pages/GuidedJourney";
import DocumentVault from "./pages/DocumentVault";
import MyApplications from "./pages/MyApplications";
import ResolutionPlanner from "./pages/ResolutionPlanner";

function ComingSoon({ title }: { title: string }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-8 dark:border-[#293956] dark:bg-[#18243B]">
      <p className="text-xs font-bold uppercase tracking-widest text-[#147d83] dark:text-[#2FE9C2]">
        Page unavailable
      </p>

      <h1 className="mt-3 text-3xl font-bold text-[#173f68] dark:text-slate-100">
        {title}
      </h1>

      <p className="mt-3 text-slate-600 dark:text-slate-400">
        The requested page is not available in this workspace.
      </p>
    </section>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="services" element={<Services />} />
          <Route path="documents" element={<DocumentVault />} />
          <Route path="applications" element={<MyApplications />} />
          <Route path="planner" element={<ResolutionPlanner />} />
          <Route
            path="services/passport/journey"
            element={<GuidedJourney />}
          />
          <Route
            path="services/:serviceId"
            element={<ServiceDetail />}
          />
          <Route
            path="*"
            element={<ComingSoon title="Page not found" />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
