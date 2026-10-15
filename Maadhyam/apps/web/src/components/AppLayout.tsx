import { HouseholdProvider } from '../context/HouseholdContext';
import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Landmark,
  Files,
  GitBranch,
  Workflow,
  Users,
  ClipboardList,
  Menu,
  X,
  ShieldCheck,
  PanelLeftClose,
  PanelLeftOpen,
  Moon,
  Sun,
} from "lucide-react";
import AIAssistant from "./AIAssistant";
import { DocumentProvider } from "../context/DocumentContext";
import { WorkspaceProvider } from "../context/WorkspaceContext";

const navigation = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Find Services", path: "/services", icon: Landmark },
  { label: "My Documents", path: "/documents", icon: Files },
  { label: "My Applications", path: "/applications", icon: ClipboardList },
  { label: "Resolution Planner", path: "/planner", icon: GitBranch },
  { label: "Household Intelligence", path: "/household", icon: Users },
  { label: "Citizen Workflows", path: "/workflows", icon: Workflow },
];

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [appearance, setAppearance] = useState<"light" | "dark">(() => {
    let saved:string|null=null;
    try {saved=localStorage.getItem("maadhyam-appearance");}catch { /* Private mode may deny storage. */ }
    return saved === "dark" ? "dark" : "light";
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", appearance === "dark");
    try {localStorage.setItem("maadhyam-appearance", appearance);}catch { /* Appearance remains usable in memory. */ }
  }, [appearance]);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <DocumentProvider>
      <WorkspaceProvider>
      <HouseholdProvider>
      <div className="min-h-screen bg-[#f5f7fa]">
        {mobileOpen && (
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}

        <aside
          className={`fixed inset-y-0 left-0 z-40 flex flex-col
            border-r border-slate-200 bg-white
            transition-[width,transform] duration-300 ease-in-out
            w-64
            ${collapsed ? "lg:w-20" : "lg:w-64"}
            lg:translate-x-0
            ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <div
            className={`flex h-20 shrink-0 items-center
              border-b border-slate-100 px-4
              ${collapsed ? "lg:justify-center" : "justify-between"}`}
          >
            <NavLink
              to="/"
              aria-label="Maadhyam home"
              onClick={() => setMobileOpen(false)}
              className="flex min-w-0 items-center gap-3"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#173f68] text-white">
                <Landmark size={24} />
              </div>
              <div className={collapsed ? "lg:hidden" : ""}>
                <div className="text-xl font-bold tracking-tight text-[#173f68]">Maadhyam</div>
                <div className="text-xs text-slate-500">माध्यम</div>
              </div>
            </NavLink>
            <button
              type="button"
              aria-label="Close mobile menu"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg p-2 hover:bg-slate-100 lg:hidden"
            >
              <X size={20} />
            </button>
          </div>

          <div className={`pt-7 ${collapsed ? "lg:px-3" : "px-5"}`}>
            <p
              className={`mb-4 px-3 text-xs font-semibold uppercase
                tracking-widest text-slate-400
                ${collapsed ? "lg:hidden" : ""}`}
            >
              Workspace
            </p>
            <nav aria-label="Main navigation" className="space-y-1">
              {navigation.map(({ label, path, icon: Icon }) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/"}
                  title={label}
                  aria-label={label}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center rounded-xl py-3
                      text-sm font-medium transition-colors
                      ${
                        collapsed
                          ? "gap-3 px-4 lg:justify-center lg:gap-0 lg:px-0"
                          : "gap-3 px-4"
                      }
                      ${
                        isActive
                          ? "bg-[#eaf3f5] text-[#126a70]"
                          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                      }`
                  }
                >
                  <Icon size={19} className="shrink-0" />
                  <span className={`whitespace-nowrap ${collapsed ? "lg:hidden" : ""}`}>
                    {label}
                  </span>
                </NavLink>
              ))}
            </nav>
          </div>

          <div className={`mt-auto p-5 ${collapsed ? "lg:hidden" : ""}`}>
            <div className="rounded-2xl bg-[#edf5f4] p-4">
              <ShieldCheck className="mb-2 text-[#147d83]" size={22} />
              <p className="text-sm font-semibold text-[#173f68]">Guidance you can verify</p>
              <p className="mt-2 text-xs leading-5 text-slate-600">
                Maadhyam is an independent assistance platform,
                not an official government website.
              </p>
            </div>
          </div>
        </aside>

        <div
          className={`transition-[padding] duration-300 ease-in-out ${
            collapsed ? "lg:pl-20" : "lg:pl-64"
          }`}
        >
          <header
            className="sticky top-0 z-20 flex h-20 items-center
              justify-between border-b border-slate-200
              bg-white/95 px-5 backdrop-blur md:px-9"
          >
            <div className="flex items-center gap-4">
              <button
                type="button"
                aria-label="Open navigation"
                aria-expanded={mobileOpen}
                onClick={() => setMobileOpen(true)}
                className="rounded-lg p-2 hover:bg-slate-100 lg:hidden"
              >
                <Menu size={23} />
              </button>
              <button
                type="button"
                onClick={() => setCollapsed((previous) => !previous)}
                aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                aria-expanded={!collapsed}
                title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                className="hidden rounded-lg p-2 text-slate-600
                  transition hover:bg-slate-100 lg:inline-flex"
              >
                {collapsed ? <PanelLeftOpen size={21} /> : <PanelLeftClose size={21} />}
              </button>
              <div>
                <p className="text-sm font-semibold text-[#173f68]">Citizen Workspace</p>
                <p className="hidden text-xs text-slate-500 sm:block">
                  Understand. Prepare. Resolve.
                </p>
              </div>
            </div>
            <div className="ml-auto flex shrink-0 items-center justify-end gap-3">
              <button
                type="button"
                aria-label={appearance === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                aria-pressed={appearance === "dark"}
                title={appearance === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                onClick={() => setAppearance(previous => previous === "dark" ? "light" : "dark")}
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-[#173f68] transition-colors hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#147d83] dark:border-slate-600 dark:bg-[#203440] dark:text-white dark:hover:bg-[#2a4554]"
              >
                {appearance === "dark" ? <Sun size={19} aria-hidden="true" /> : <Moon size={19} aria-hidden="true" />}
              </button>
              <span className="inline-flex h-9 shrink-0 items-center rounded-full bg-[#edf5f4] px-3 text-xs font-semibold text-[#126a70]">
                Preview
              </span>
            </div>
          </header>

          <main className="mx-auto w-full max-w-[1800px] px-5 py-8 md:px-9 md:py-10 xl:px-12">
            <Outlet />
          </main>
        </div>
        <AIAssistant />
      </div>
          </HouseholdProvider>
      </WorkspaceProvider>
    </DocumentProvider>
  );
}
