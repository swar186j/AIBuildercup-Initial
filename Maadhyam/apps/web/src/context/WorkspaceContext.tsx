/* eslint react-refresh/only-export-components: ["error", { "allowExportNames": ["useWorkspace", "plannerTasks"] }] */
import { newJourney, readJourney, type JourneyData } from './preparationStorage';
import type { PassportAssistanceType } from '../data/journeyData';
import { createContext, useContext, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useDocuments } from "./DocumentContext";
import { useAuth } from './AuthContext';
import { auth } from '../services/firebase';
import { createCloudApplication, deleteCloudApplication, getCloudPlanner, listCloudApplications, putCloudPlanner, resetCloudPlanner, updateCloudApplication, type CloudApplication, type DraftPayload } from '../services/m10Applications';

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

type WorkspaceValue = {
  applications: Application[];
  createDraft: (type?: PassportAssistanceType) => Promise<string>;
  updatePreparation: (id:string, patch:Partial<JourneyData>) => void;
  preparationSaving:boolean;
  storageNotice:string;
  setPreparationSaving:(enabled:boolean) => void;
  deletePreparation:(id:string) => void;
  plannerCompleted: string[];
  togglePlannerTask: (id: string) => void;
  resetPlanner: () => void;
  cloudReady: boolean;
  cloudBusy: boolean;
  cloudLoading: boolean;
  cloudSaving: boolean;
  hasUnsavedChanges: boolean;
  retryCloud: () => void;
};
function applicationFor(id:string,journey:JourneyData):Application {
 const names:Record<PassportAssistanceType,string>={fresh:'New passport preparation',reissue:'Passport reissue preparation',correction:'Passport correction preparation',documents:'Passport document preparation',police:'Police verification preparation'};
 return {id,service:'Passport',type:names[journey.assistanceType],status:journey.stepIndex===3?'completed':journey.stepIndex===0?'draft':'in-progress',completedSteps:journey.stepIndex===3?4:journey.stepIndex,totalSteps:4,nextAction:journey.stepIndex===3?'Review your saved preparation summary':'Resume your guided questionnaire',updated:'Syncing with your account',steps:['Select assistance type','Answer guided questions','Review document readiness','Prepare next steps'],journey};
}
const WorkspaceContext = createContext<WorkspaceValue | null>(null);

function cloudPayload(id: string, journey: JourneyData): DraftPayload {
  return {
    client_id: /^LOCAL-[A-Za-z0-9-]{8,100}$/.test(id) ? id : undefined,
    service_type: 'passport', application_type: journey.assistanceType,
    status: journey.stepIndex === 3 ? 'completed' : journey.stepIndex === 0 ? 'draft' : 'in-progress',
    applicant_details: { name: journey.applicantName, date_of_birth: journey.applicantDob },
    questionnaire_answers: journey.answers, current_step: journey.stepIndex,
    selected_document_ids: journey.documentIds, rule_pack_version: 'unverified',
  };
}
function fromCloud(record: CloudApplication): Application | null {
  if (record.service_type !== 'passport') return null;
  const journey = readJourney({
    schemaVersion: 1, service: 'passport', assistanceType: record.application_type,
    answers: record.questionnaire_answers, stepIndex: record.current_step,
    applicantName: record.applicant_details?.name ?? '',
    applicantDob: record.applicant_details?.date_of_birth ?? '',
    documentIds: record.selected_document_ids || [],
  });
  return journey ? { ...applicationFor(record.id, journey), updated: 'Saved to your account' } : null;
}
function toMessage(error: unknown) { return error instanceof Error ? error.message : 'Unknown network error'; }

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { user, registerLogoutGuard } = useAuth();
  const uid = user?.uid;
  const [applications, setApplications] = useState<Application[]>([]);
  const applicationsRef = useRef(applications);
  const [cloudReady, setCloudReady] = useState(false);
  const [cloudLoading, setCloudLoading] = useState(true);
  const [reloadAttempt, setReloadAttempt] = useState(0);
  const [cloudBusy, setCloudBusy] = useState(false);
  const [pendingWrites, setPendingWrites] = useState(0);
  const [pendingDebounces, setPendingDebounces] = useState(0);
  const [unsavedCount, setUnsavedCount] = useState(0);
  const savedJourneys = useRef(new Map<string, string>());
  const unsavedIds = useRef(new Set<string>());
  const creatingRef = useRef(false);
  const pendingDraft = useRef<{ id: string; uid: string; journey: JourneyData } | null>(null);
  const [storageNotice, setStorageNotice] = useState('Loading your saved preparations…');
  const [manuallyCompleted, setManuallyCompleted] = useState<string[]>([]);
  const revisionRef = useRef(new Map<string, number>());
  const plannerRevision = useRef(0);
  const queueRef = useRef(new Map<string, Promise<unknown>>());
  const timersRef = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const deletedRef = useRef(new Set<string>());
  const sessionId = useRef(0);
  const { documents } = useDocuments();

  useEffect(() => {
    if (!cloudBusy && pendingWrites === 0 && pendingDebounces === 0 && unsavedCount === 0) return;
    const preventLostSave = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', preventLostSave);
    return () => window.removeEventListener('beforeunload', preventLostSave);
  }, [cloudBusy, pendingWrites, pendingDebounces, unsavedCount]);

  useEffect(() => registerLogoutGuard(() => !cloudBusy && pendingWrites === 0 && pendingDebounces === 0 && unsavedCount === 0),
    [registerLogoutGuard, cloudBusy, pendingWrites, pendingDebounces, unsavedCount]);

  const assignApplications = useCallback((next: Application[]) => {
    applicationsRef.current = next;
    setApplications(next);
  }, []);

  const reloadCloud = useCallback(async (expectedUid: string, session: number) => {
    const [remote, planner] = await Promise.all([listCloudApplications(), getCloudPlanner()]);
    if (session !== sessionId.current || auth?.currentUser?.uid !== expectedUid) return;
    const valid = remote.flatMap(record => {
      const normalized = fromCloud(record);
      return normalized ? [normalized] : [];
    });
    revisionRef.current = new Map(remote.map(item => [item.id, item.revision]));
    plannerRevision.current = planner.revision;
    setManuallyCompleted(planner.completed.filter(id => plannerTasks.some(task => task.id === id)));
    assignApplications(valid);
    savedJourneys.current = new Map(valid.map(item => [item.id, JSON.stringify(item.journey)]));
    unsavedIds.current.clear();
    setUnsavedCount(0);
    setStorageNotice('Preparations saved under your Firebase account. Changes sync to Firestore.');
    setCloudReady(true);
  }, [assignApplications]);

  useEffect(() => {
    sessionId.current += 1;
    const current = sessionId.current;
    revisionRef.current.clear(); queueRef.current.clear(); deletedRef.current.clear();
    savedJourneys.current.clear(); unsavedIds.current.clear();
    if (pendingDraft.current?.uid !== uid) pendingDraft.current = null;
    const timers = timersRef.current;
    for (const timer of timers.values()) clearTimeout(timer);
    timers.clear();
    queueMicrotask(() => {
      if (sessionId.current !== current) return;
      assignApplications([]);
      setCloudReady(false);
      setCloudLoading(true);
      setPendingWrites(0);
      setPendingDebounces(0);
      setUnsavedCount(0);
      setCloudBusy(false);
      creatingRef.current = false;
      setManuallyCompleted([]);
      if (!uid) { setStorageNotice('Sign in to save preparations.'); setCloudLoading(false); return; }
      void reloadCloud(uid, current).catch(error => {
        if (sessionId.current !== current) return;
        setStorageNotice(`Cloud loading failed: ${toMessage(error)}. Do not create a new preparation until connected.`);
        setCloudReady(false);
      }).finally(() => {
        if (sessionId.current === current) setCloudLoading(false);
      });
    });
    return () => {
      sessionId.current += 1;
      for (const timer of timers.values()) clearTimeout(timer);
    };
  }, [uid, reloadCloud, assignApplications, reloadAttempt]);

  const schedule = useCallback((id: string, operation: () => Promise<void>) => {
    const session = sessionId.current;
    setPendingWrites(count => count + 1);
    const earlier = queueRef.current.get(id) || Promise.resolve();
    const next = earlier.catch(() => { /* error already reported */ }).then(operation).catch(error => {
      if (session !== sessionId.current) return;
      setStorageNotice(`Cloud save failed for ${id}: ${toMessage(error)}. Your changes may not survive reload. Retry after checking connectivity.`);
    }).finally(() => {
      if (session === sessionId.current) setPendingWrites(count => Math.max(0, count - 1));
      if (queueRef.current.get(id) === next) queueRef.current.delete(id);
    });
    queueRef.current.set(id, next);
  }, []);
  const createDraft = useCallback(async (type: PassportAssistanceType = 'fresh'): Promise<string> => {
    if (!uid || !cloudReady || auth?.currentUser?.uid !== uid) throw new Error('Wait for Firestore to connect before starting a preparation.');
    if (creatingRef.current) throw new Error('A preparation is already being created.');
    creatingRef.current = true;
    // A response can be lost after Firestore commits. Reuse the creation key on
    // retry so that this ambiguous outcome never creates a duplicate draft.
    if (!pendingDraft.current || pendingDraft.current.uid !== uid || pendingDraft.current.journey.assistanceType !== type) {
      pendingDraft.current = { id: `LOCAL-${crypto.randomUUID()}`, uid, journey: { ...newJourney(type), documentIds: documents.map(d => d.id) } };
    }
    const { id, journey } = pendingDraft.current;
    const session = sessionId.current;
    setCloudBusy(true);
    try {
        const created = await createCloudApplication(cloudPayload(id, journey));
        if (session !== sessionId.current || auth?.currentUser?.uid !== uid) throw new Error('Your sign-in session changed.');
        revisionRef.current.set(id, created.revision);
        const confirmed = fromCloud(created) || applicationFor(id, journey);
        savedJourneys.current.set(id, JSON.stringify(confirmed.journey));
        pendingDraft.current = null;
        assignApplications([confirmed, ...applicationsRef.current.filter(item => item.id !== id)]);
        setStorageNotice('New draft saved to your account.');
        return id;
    } catch (error) {
      if (session === sessionId.current) setStorageNotice(`Draft creation failed: ${toMessage(error)}`);
      throw error;
    } finally {
      if (session === sessionId.current) { setCloudBusy(false); creatingRef.current = false; }
    }
  }, [uid, cloudReady, documents, assignApplications]);

  const saveLatest = useCallback((id: string) => {
    const previous = timersRef.current.get(id);
    if (previous) clearTimeout(previous);
    const session = sessionId.current;
    const timer = setTimeout(() => {
      timersRef.current.delete(id);
      setPendingDebounces(timersRef.current.size);
      if (deletedRef.current.has(id)) return;
      schedule(id, async () => {
        if (session !== sessionId.current || !uid || auth?.currentUser?.uid !== uid || deletedRef.current.has(id)) return;
        const item = applicationsRef.current.find(record => record.id === id);
        const rev = revisionRef.current.get(id);
        if (!item?.journey || rev === undefined) throw new Error('Draft creation is not confirmed yet');
        const updated = await updateCloudApplication(id, rev, cloudPayload(id, item.journey));
        if (session !== sessionId.current) return;
        revisionRef.current.set(id, updated.revision);
        savedJourneys.current.set(id, JSON.stringify(item.journey));
        const latest = applicationsRef.current.find(record => record.id === id);
        if (JSON.stringify(latest?.journey) === savedJourneys.current.get(id)) unsavedIds.current.delete(id);
        setUnsavedCount(unsavedIds.current.size);
        setStorageNotice('Latest preparation changes saved to Firestore.');
      });
    }, 350);
    timersRef.current.set(id, timer);
    setPendingDebounces(timersRef.current.size);
  }, [uid, schedule]);

  const updatePreparation = useCallback((id: string, patch: Partial<JourneyData>) => {
    if (pendingDraft.current && savedJourneys.current.has(pendingDraft.current.id)) pendingDraft.current = null;
    const next = applicationsRef.current.map(app => {
      if (app.id !== id || !app.journey) return app;
      const journey = readJourney({ ...app.journey, ...patch });
      return journey ? applicationFor(id, journey) : app;
    });
    const updated = next.find(app => app.id === id);
    if (!updated?.journey) return;
    if (JSON.stringify(updated.journey) === savedJourneys.current.get(id) && !unsavedIds.current.has(id)) return;
    unsavedIds.current.add(id);
    setUnsavedCount(unsavedIds.current.size);
    assignApplications(next);
    setStorageNotice('Saving your latest changes…');
    saveLatest(id);
  }, [assignApplications, saveLatest]);
  function deletePreparation(id: string) {
    const existing = applicationsRef.current.find(item => item.id === id);
    if (!existing?.journey) return;
    const timer = timersRef.current.get(id);
    if (timer) clearTimeout(timer);
    timersRef.current.delete(id);
    setPendingDebounces(timersRef.current.size);
    deletedRef.current.add(id);
    const session = sessionId.current;
    schedule(id, async () => {
      if (session !== sessionId.current || !uid || auth?.currentUser?.uid !== uid) return;
      const revision = revisionRef.current.get(id);
      if (revision === undefined) throw new Error('Draft creation was not confirmed; refresh and retry removal');
      try { await deleteCloudApplication(id, revision); }
      catch (error) { deletedRef.current.delete(id); throw error; }
      if (session !== sessionId.current) return;
      assignApplications(applicationsRef.current.filter(item => item.id !== id));
      revisionRef.current.delete(id);
      savedJourneys.current.delete(id);
      unsavedIds.current.delete(id);
      setUnsavedCount(unsavedIds.current.size);
      setStorageNotice('Preparation deleted from Firestore.');
    });
  }

  const plannerCompleted = useMemo(() => {
    const done = new Set(manuallyCompleted);
    return plannerTasks.filter(t => done.has(t.id)).map(t => t.id);
  }, [manuallyCompleted]);
  function togglePlannerTask(id: string) {
    if (!uid || !cloudReady) return;
    const task = plannerTasks.find(t => t.id === id);
    if (!task) return;
    const done = new Set(plannerCompleted);
    const completing = !done.has(id);
    if (completing && !task.dependsOn.every(dep => done.has(dep))) return;
    const session = sessionId.current;
    schedule('workspace-planner', async () => {
      if (session !== sessionId.current || auth?.currentUser?.uid !== uid) return;
      try {
        const result = await putCloudPlanner(plannerRevision.current, id, completing);
        if (session !== sessionId.current) return;
        plannerRevision.current = result.revision;
        setManuallyCompleted(result.completed);
        setStorageNotice('Planner progress saved.');
      } catch (error) {
        setStorageNotice(`Planner update failed: ${toMessage(error)}. Reload to reconcile.`);
        throw error;
      }
    });
  }
  function resetPlanner() {
    if (!uid || !cloudReady) return;
    const session = sessionId.current;
    schedule('workspace-planner', async () => {
      if (session !== sessionId.current || auth?.currentUser?.uid !== uid) return;
      const result = await resetCloudPlanner(plannerRevision.current);
      if (session !== sessionId.current) return;
      plannerRevision.current = result.revision;
      setManuallyCompleted(result.completed);
      setStorageNotice('Planner progress cleared from Firestore.');
    });
  }

  // Browser-local saving is superseded by per-user Firestore storage. Keep the
  // former context fields for GuidedJourney compatibility, but do not claim
  // browser storage controls can switch Firestore writes off.
  const setPreparationSaving = () => {
    setStorageNotice('Preparations are saved to your account in Firestore.');
  };
  return <WorkspaceContext.Provider value={{
    applications, createDraft, updatePreparation,
    preparationSaving: cloudReady, storageNotice, setPreparationSaving, deletePreparation,
    plannerCompleted, togglePlannerTask, resetPlanner, cloudReady, cloudBusy,
    cloudLoading, cloudSaving: pendingWrites > 0 || pendingDebounces > 0, hasUnsavedChanges: unsavedCount > 0,
    retryCloud: () => { setCloudReady(false); setCloudLoading(true); setReloadAttempt(attempt => attempt + 1); },
  }}>{children}</WorkspaceContext.Provider>;
}
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error('useWorkspace must be used inside WorkspaceProvider');
  return context;
}
