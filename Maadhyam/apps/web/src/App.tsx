import HouseholdIntelligence from './pages/HouseholdIntelligence';
import { Component, type ReactNode } from "react";

import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Services from "./pages/Services";
import ServiceDetail from "./pages/ServiceDetail";
import GuidedJourney from "./pages/GuidedJourney";
import DocumentVault from "./pages/DocumentVault";
import MyApplications from "./pages/MyApplications";
import ResolutionPlanner from "./pages/ResolutionPlanner";
import CitizenWorkflows from "./pages/CitizenWorkflows";

class PlannerErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean; errorMessage: string }> {
  state = { failed: false, errorMessage: "" };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error) { console.error('Resolution Planner rendering error:', error); this.setState({ errorMessage: error.message }); }
  render() {
    if (this.state.failed) return (
      <section role="alert" className="mx-auto max-w-5xl rounded-2xl border border-amber-300 bg-white p-6 text-[#173f68] dark:bg-[#18243B] dark:text-white">
        <h1 className="text-2xl font-bold">Resolution Planner needs a refresh</h1>
        <p className="mt-3 text-sm">We couldn't display the planning analysis. Your Vault records have not been deleted. Please retry; if the issue continues, check the browser console and backend response.</p>
        <p className="mt-3 text-xs text-amber-700">Diagnostic: {this.state.errorMessage || 'Rendering error. Check browser console for details.'}</p>
        <button type="button" className="mt-4 rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white" onClick={() => this.setState({ failed: false })}>Retry planner</button>
      </section>
    );
    return this.props.children;
  }
}

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
          <Route path="planner" element={<PlannerErrorBoundary><ResolutionPlanner /></PlannerErrorBoundary>} />
          <Route path="household" element={<HouseholdIntelligence />} />
          <Route path="workflows" element={<CitizenWorkflows />} />
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
