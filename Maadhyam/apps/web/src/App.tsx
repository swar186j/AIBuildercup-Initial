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
    <section className="rounded-2xl border border-slate-200 bg-white p-8">
      <p className="text-xs font-bold uppercase tracking-widest text-[#147d83]">
        In development
      </p>
      <h1 className="mt-3 text-3xl font-bold text-[#173f68]">{title}</h1>
      <p className="mt-3 text-slate-600">
        This workspace will be implemented in an upcoming frontend phase.
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
          <Route path="services/passport/journey" element={<GuidedJourney />} />
          <Route path="services/:serviceId" element={<ServiceDetail />} />
          <Route path="*" element={<ComingSoon title="Page not found" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
