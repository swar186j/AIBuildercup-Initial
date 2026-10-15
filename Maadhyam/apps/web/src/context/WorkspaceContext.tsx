import { applicationApi, type SavedApplication } from "../services/applicationApi";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Status = "draft" | "in-progress" | "completed";
export type Application = {
  id: string;
  service: string;
  type: string;
  status: Status;
  completedSteps: number;
  totalSteps: number;
  nextAction: string;
  updated: string;
  steps: string[];
};

const defaultSteps = ["Select assistance type", "Answer guided questions", "Review document readiness", "Prepare next steps"];
function fromBackend(saved: SavedApplication): Application {
  // Backend payload is untrusted; never assume it has frontend display fields.
  const kind = saved.kind.toLowerCase();
  const type = kind === "reissue" ? "Passport reissue preparation" : kind === "fresh" ? "Fresh passport preparation" : "Passport preparation";
  return {
    id: saved.id, service: "Passport", type, status: saved.status,
    completedSteps: 0, totalSteps: 4,
    nextAction: "Start the passport guided journey",
    updated: `Backend draft · ${new Date(saved.updated_at).toLocaleDateString()}`,
    steps: defaultSteps,
  };
}

const initialApplications: Application[] = [
  {
    id: "DEMO-001", service: "Passport", type: "Fresh passport preparation", status: "in-progress",
    completedSteps: 2, totalSteps: 4, nextAction: "Review identity and address documents",
    updated: "Demo record", steps: ["Select assistance type", "Answer guided questions", "Review document readiness", "Prepare next steps"],
  },
  {
    id: "DEMO-002", service: "Passport", type: "Passport reissue preparation", status: "draft",
    completedSteps: 1, totalSteps: 4, nextAction: "Complete the guided questionnaire",
    updated: "Demo record", steps: ["Select assistance type", "Answer guided questions", "Review document readiness", "Prepare next steps"],
  },
  {
    id: "DEMO-003", service: "Passport", type: "Document preparation checklist", status: "completed",
    completedSteps: 4, totalSteps: 4, nextAction: "Review the saved preparation summary",
    updated: "Demo record", steps: ["Select assistance type", "Answer guided questions", "Review document readiness", "Prepare next steps"],
  },
];

export const plannerTasks = [
  { id: "journey", title: "Complete your passport preparation questionnaire", description: "Select the assistance type and review your answers. This is a preparation step, not an official application.", dependsOn: [] as string[], action: "Open guided journey", href: "/services/passport/journey" },
  { id: "vault", title: "Organize sample supporting documents", description: "Upload fictional test files, assign categories and identify their holders.", dependsOn: ["journey"], action: "Open Document Vault", href: "/documents" },
  { id: "details", title: "Review document details", description: "Check the name, birth date and address you entered or accepted from the demo extraction.", dependsOn: ["vault"], action: "Review documents", href: "/documents" },
  { id: "differences", title: "Review potential discrepancies", description: "Run the document comparison and inspect possible differences. A flag does not establish an error or fraud.", dependsOn: ["details"], action: "Analyze documents", href: "/documents" },
  { id: "next", title: "Prepare your next-step checklist", description: "Revisit the guided journey and check current instructions on the relevant official portal before taking action.", dependsOn: ["differences"], action: "View journey", href: "/services/passport/journey" },
];

type WorkspaceValue = {
  applications: Application[];
  createDraft: () => Promise<{ id: string; savedToBackend: boolean }>;
  backendState: "loading" | "connected" | "offline";
  plannerCompleted: string[];
  togglePlannerTask: (id: string) => void;
  resetPlanner: () => void;
};
const STORAGE_KEY = "maadhyam.workspace.v1";

type SavedWorkspace = { applications: Application[]; plannerCompleted: string[] };
function loadWorkspace(): SavedWorkspace {
  const fallback = { applications: initialApplications, plannerCompleted: [] as string[] };
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return fallback;
    const saved: unknown = JSON.parse(raw);
    if (!saved || typeof saved !== "object") return fallback;
    const data = saved as Partial<SavedWorkspace>;
    const applications = Array.isArray(data.applications) && data.applications.every((item) =>
      item && typeof item === "object" && typeof item.id === "string" &&
      typeof item.service === "string" && typeof item.type === "string" &&
      ["draft", "in-progress", "completed"].includes(item.status) &&
      typeof item.completedSteps === "number" && typeof item.totalSteps === "number" &&
      typeof item.nextAction === "string" && typeof item.updated === "string" &&
      Array.isArray(item.steps) && item.steps.every((step: unknown) => typeof step === "string")
    ) ? data.applications : fallback.applications;
    const validTaskIds = new Set(plannerTasks.map((task) => task.id));
    const plannerCompleted = Array.isArray(data.plannerCompleted)
      ? data.plannerCompleted.filter((id): id is string => typeof id === "string" && validTaskIds.has(id))
      : [];
    return { applications, plannerCompleted };
  } catch {
    return fallback;
  }
}

const WorkspaceContext = createContext<WorkspaceValue | null>(null);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [initial] = useState(loadWorkspace);
  const [applications, setApplications] = useState<Application[]>(initial.applications);
  const [plannerCompleted, setPlannerCompleted] = useState<string[]>(initial.plannerCompleted);
  const [backendState, setBackendState] = useState<"loading" | "connected" | "offline">("loading");
  useEffect(() => {
    let active = true;
    applicationApi.list().then((remote) => {
      if (!active) return;
      const mapped = remote.map(fromBackend);
      setApplications(previous => {
        const remoteIds = new Set(mapped.map(app => app.id));
        return [...mapped, ...previous.filter(app => !remoteIds.has(app.id))];
      });
      setBackendState("connected");
    }).catch(() => { if (active) setBackendState("offline"); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ applications, plannerCompleted }));
    } catch {
      // Storage may be disabled or full; keep the workspace usable for this session.
    }
  }, [applications, plannerCompleted]);
  async function createDraft(): Promise<{ id: string; savedToBackend: boolean }> {
    try {
      const saved = await applicationApi.create("fresh");
      setApplications(previous => [fromBackend(saved), ...previous.filter(app => app.id !== saved.id)]);
      setBackendState("connected");
      return { id: saved.id, savedToBackend: true };
    } catch {
      const id = `LOCAL-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      setApplications(previous => [{
        id, service: "Passport", type: "New passport preparation", status: "draft",
        completedSteps: 0, totalSteps: 4, nextAction: "Start the passport guided journey",
        updated: "Saved in this browser", steps: defaultSteps,
      }, ...previous]);
      setBackendState("offline");
      return { id, savedToBackend: false };
    }
  }
  function togglePlannerTask(id: string) {
    setPlannerCompleted((previous) => {
      const completed = new Set(previous);
      if (completed.has(id)) {
        const removed = new Set([id]);
        let changed = true;
        while (changed) {
          changed = false;
          for (const task of plannerTasks) {
            if (!removed.has(task.id) && task.dependsOn.some((dependency) => removed.has(dependency))) {
              removed.add(task.id); changed = true;
            }
          }
        }
        return previous.filter((item) => !removed.has(item));
      }
      const task = plannerTasks.find((item) => item.id === id);
      if (!task || !task.dependsOn.every((dependency) => completed.has(dependency))) return previous;
      return [...previous, id];
    });
  }
  return <WorkspaceContext.Provider value={{ applications, createDraft, backendState, plannerCompleted, togglePlannerTask, resetPlanner: () => setPlannerCompleted([]) }}>{children}</WorkspaceContext.Provider>;
}
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return context;
}
