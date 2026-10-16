import { createContext, useContext } from "react";
import type { PassportAssistanceType } from "../data/journeyData";
import type { JourneyData } from "./preparationStorage";
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
  journey?: JourneyData;
};

export const plannerTasks = [
  { id: "journey", title: "Complete your passport preparation questionnaire", description: "Select the assistance type and review your answers. This is a preparation step, not an official application.", dependsOn: [] as string[], action: "Open guided journey", href: "/services/passport/journey" },
  { id: "vault", title: "Organize sample supporting documents", description: "Upload fictional test files, assign categories and identify their holders.", dependsOn: ["journey"], action: "Open Document Vault", href: "/documents" },
  { id: "details", title: "Review document details", description: "Check the name, birth date and address you entered or accepted from the demo extraction.", dependsOn: ["vault"], action: "Review documents", href: "/documents" },
  { id: "differences", title: "Review potential discrepancies", description: "Run the document comparison and inspect possible differences. A flag does not establish an error or fraud.", dependsOn: ["details"], action: "Analyze documents", href: "/documents" },
  { id: "next", title: "Prepare your next-step checklist", description: "Revisit the guided journey and check current instructions on the relevant official portal before taking action.", dependsOn: ["differences"], action: "View journey", href: "/services/passport/journey" },
];

export type WorkspaceValue = {
  applications: Application[];
  createDraft: (type?: PassportAssistanceType) => string;
  updatePreparation: (id:string, patch:Partial<JourneyData>) => void;
  preparationSaving:boolean;
  storageNotice:string;
  setPreparationSaving:(enabled:boolean) => void;
  deletePreparation:(id:string) => void;
  /** Explicit cloud save; never runs on ordinary edits or on browser-local opt-in. */
  savePreparationToCloud:(id:string,patch:Partial<JourneyData>) => Promise<string>;
  cloudRestoring:boolean;
  cloudRestoreFailed:boolean;
  restorePreparationFromCloud:(id:string) => Promise<boolean>;
  activateSavedPreparation:(id:string) => Promise<void>;
  activeCloudPreparationId:string|null;
  saveHouseholdToCloud:()=>Promise<string>;
  plannerCompleted: string[];
  togglePlannerTask: (id: string) => void;
  resetPlanner: () => void;
  plannerTargetDate: string;
  setPlannerTargetDate: (value:string) => void;
  recordPlannerAnalysis: (taskIds:string[], findingCount:number, sourceUrl:string, documentIds:string[]) => void;
};
export const WorkspaceContext = createContext<WorkspaceValue | null>(null);
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return context;
}
