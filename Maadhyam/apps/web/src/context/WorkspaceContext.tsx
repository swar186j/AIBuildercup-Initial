import { createContext, useContext, useState, type ReactNode } from "react";

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
  createDraft: () => string;
  plannerCompleted: string[];
  togglePlannerTask: (id: string) => void;
  resetPlanner: () => void;
};
const WorkspaceContext = createContext<WorkspaceValue | null>(null);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [applications, setApplications] = useState<Application[]>(initialApplications);
  const [plannerCompleted, setPlannerCompleted] = useState<string[]>([]);
  function createDraft() {
    const id = `LOCAL-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    setApplications((previous) => [{
      id, service: "Passport", type: "New passport preparation", status: "draft",
      completedSteps: 0, totalSteps: 4, nextAction: "Start the passport guided journey",
      updated: "Created this session", steps: ["Select assistance type", "Answer guided questions", "Review document readiness", "Prepare next steps"],
    }, ...previous]);
    return id;
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
  return <WorkspaceContext.Provider value={{ applications, createDraft, plannerCompleted, togglePlannerTask, resetPlanner: () => setPlannerCompleted([]) }}>{children}</WorkspaceContext.Provider>;
}
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return context;
}
