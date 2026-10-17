import { subscribePersistence, persistenceFailure, clearPersistenceFailure, persistPreparations } from "./preparationPersistence";
import { WorkspaceContext, plannerTasks, type Application } from "./WorkspaceContext";
import { newJourney, readJourney, PREPARATION_KEY, PREPARATION_CONSENT, type JourneyData } from './preparationStorage';
import type { PassportAssistanceType } from '../data/journeyData';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { useDocuments } from "./DocumentContext";
import { cloudApplications, type CloudApplication, type PlannerCloudState, type AssessmentCloudEntry } from '../services/cloudApplications';
import { useHousehold } from './HouseholdContext';
import { cloudToPreparation, preparationToCloud, sameCloudPreparation } from '../services/cloudPreparation';

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

function applicationFor(id:string,journey:JourneyData):Application {
 const names:Record<PassportAssistanceType,string>={fresh:'New passport preparation',reissue:'Passport reissue preparation',correction:'Passport correction preparation',documents:'Passport document preparation',police:'Police verification preparation'};
 return {id,createdAt:journey.createdAt,lastSavedAt:journey.lastSavedAt,service:'Passport',type:names[journey.assistanceType],status:journey.stepIndex===3?'completed':journey.stepIndex===0?'draft':'in-progress',completedSteps:journey.stepIndex===3?4:journey.stepIndex,totalSteps:4,nextAction:journey.stepIndex===3?'Review your saved preparation summary':'Resume your guided questionnaire',updated:'Saved in this workspace',steps:['Select assistance type','Answer guided questions','Review document readiness','Prepare next steps'],journey};
}
const CLOUD_CONSENT_KEY = 'maadhyam-cloud-preparations-consent-v1';
const CLOUD_WORKSPACE_CONSENT_KEY = 'maadhyam-cloud-workspace-consent-v2';
function previousCloudConsent():boolean {
  try { return localStorage.getItem(CLOUD_CONSENT_KEY) === 'yes'; }
  catch { return false; }
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [loaded] = useState(() => {
    try {
      if(localStorage.getItem(PREPARATION_CONSENT)!=='yes')return {enabled:false,records:[] as Application[],notice:''};
      const raw=localStorage.getItem(PREPARATION_KEY);
      if(!raw)return {enabled:true,records:[] as Application[],notice:''};
      const data=JSON.parse(raw);
      if(data.schemaVersion!==1||!Array.isArray(data.records)||data.records.length>100)throw new Error('Unsupported saved format');
      const seen=new Set<string>();
      const records=data.records.map((r:unknown)=>{
        if(!r||typeof r!=='object')throw new Error('Invalid record');
        const item=r as Application;const journey=readJourney(item.journey);
        if(typeof item.id!=='string'||!/^LOCAL-[a-zA-Z0-9-]+$/.test(item.id)||seen.has(item.id)||!journey)throw new Error('Invalid saved preparation');
        seen.add(item.id);return applicationFor(item.id,journey);
      });
      return {enabled:true,records,notice:'Browser-local preparations restored. This is not government verification.'};
    } catch { return {enabled:false,records:[] as Application[],notice:'Saved preparations could not be restored (missing, malformed or outdated format). Local saving is off. Start a new preparation; existing Vault data is unchanged.'}; }
  });
  const [applications, setApplications] = useState<Application[]>([...loaded.records,...initialApplications]);
  const {members,restoreMembers,memberEditRevision}=useHousehold();
  const [manuallyCompleted, setManuallyCompleted] = useState<string[]>([]);
  const [plannerTargetDate,setPlannerTargetDate] = useState('');
  const [plannerSnapshot,setPlannerSnapshot] = useState<AssessmentCloudEntry | null>(null);
  const [history,setHistory] = useState<AssessmentCloudEntry[]>([]);
  const activeCloudId = useRef<string | null>(null);
  const [activeCloudPreparationId,setActiveCloudPreparationId] = useState<string | null>(null);
  const activateCloudId = useCallback((id:string | null) => {
    activeCloudId.current=id; setActiveCloudPreparationId(id);
  }, []);
  const cloudSyncBlocked = useRef(false);
  const lastSyncPayload = useRef('');
  const workspaceTouched = useRef(false);
  const householdEditRevision = useRef(memberEditRevision);
  useLayoutEffect(() => {
    if (householdEditRevision.current !== memberEditRevision) {
      workspaceTouched.current=true; householdEditRevision.current=memberEditRevision;
    }
  }, [memberEditRevision]);
  const membersRef=useRef(members);
  const manualRef=useRef(manuallyCompleted);
  const targetRef=useRef(plannerTargetDate);
  const snapshotRef=useRef(plannerSnapshot);
  const historyRef=useRef(history);
  const applicationsRef = useRef(applications);
  useLayoutEffect(() => {
    membersRef.current=members; manualRef.current=manuallyCompleted;
    targetRef.current=plannerTargetDate; snapshotRef.current=plannerSnapshot;
    historyRef.current=history; applicationsRef.current=applications;
  }, [members, manuallyCompleted, plannerTargetDate, plannerSnapshot, history, applications]);
  const [initialCloudConsent] = useState(previousCloudConsent);
  const cloudConsent = useRef(initialCloudConsent);
  const cloudRevisions = useRef(new Map<string,number>());
  const activeCloudSaves = useRef(new Set<string>());
  const localEditGeneration = useRef(0);
  const [cloudRestoring, setCloudRestoring] = useState(initialCloudConsent);
  const [cloudRestoreFailed,setCloudRestoreFailed] = useState(false);
  const [savingRequested,setSaving]=useState(loaded.enabled);
  const localPersistenceFailure = useSyncExternalStore(subscribePersistence, persistenceFailure, () => "");
  const preparationSaving = savingRequested && !localPersistenceFailure;
  const [storageNotice,setStorageNotice]=useState(loaded.notice);

  const workspacePayload = useCallback(() => {
    const snapshot=snapshotRef.current;
    const prior=historyRef.current;
    const historyForSave=snapshot && !prior.some(item=>item.captured_at===snapshot.captured_at)
      ? [...prior,snapshot].slice(-10) : prior;
    return {
      planner_state: {
        manual_task_ids:Array.from(new Set<string>(manualRef.current)).slice(0,100),
        target_date:targetRef.current || null,
        generated_plan:snapshot ? {task_ids:snapshot.task_ids,finding_count:snapshot.finding_count,task_count:snapshot.task_count} : {},
      } satisfies PlannerCloudState,
      household_state:{members:membersRef.current.map(m=>({...m}))},
      assessment_history:historyForSave,
    };
  }, []);
  const hydrateWorkspace = useCallback((record:CloudApplication) => {
    if (workspaceTouched.current) return;
    const planner=record.planner_state;
    if (planner && Array.isArray(planner.manual_task_ids)) {
      setManuallyCompleted(planner.manual_task_ids.filter(id=>plannerTasks.some(t=>t.id===id)));
      setPlannerTargetDate(typeof planner.target_date==='string'?planner.target_date:'');
    }
    if (Array.isArray(record.assessment_history)) {
      const recent=record.assessment_history.slice(-10);
      setHistory(recent);
      setPlannerSnapshot(recent.length ? recent[recent.length-1] : null);
    } else {
      setPlannerSnapshot(null);
    }
    restoreMembers(record.household_state?.members??[]);
  }, [restoreMembers]);
  const recordPlannerAnalysis = useCallback((taskIds:string[], findingCount:number, sourceUrl:string, documentIds:string[]) => {
    if (!Number.isInteger(findingCount) || findingCount<0 || !Array.isArray(taskIds)) return;
    const safe=taskIds.filter(id=>typeof id==='string'&&id.length<=128).slice(0,100);
    // A stable signature prevents repeated planner API renders from duplicating entries.
    const safeDocs=documentIds.filter(id=>typeof id==='string'&&id.length<=128).slice(0,60);
    if(snapshotRef.current && JSON.stringify([snapshotRef.current.task_ids,snapshotRef.current.finding_count,snapshotRef.current.input_document_ids])===JSON.stringify([safe,findingCount,safeDocs]))return;
    setPlannerSnapshot({captured_at:new Date().toISOString(),assessment_id:crypto.randomUUID(),task_count:safe.length,finding_count:Math.min(findingCount,1000),task_ids:safe,input_document_ids:safeDocs,source_url:sourceUrl.slice(0,1000),rule_pack_version:'unverified',status:'prepared'});
  }, []);
  // Cloud records are fetched only after previous, explicit remote-storage consent.
  // An incoming response cannot overwrite edits made locally while it was loading.
  useEffect(() => {
    if (!cloudConsent.current) return;
    let canceled = false;
    const generationAtStart = localEditGeneration.current;
    cloudApplications.list().then(records => {
      if (canceled) return;
      if (!Array.isArray(records)) throw new Error('Cloud application list is invalid');
      const restored: Application[] = [];
      let invalidRecords = 0;
      for (const item of records) {
        const journey = cloudToPreparation(item);
        if (!journey) { invalidRecords += 1; continue; }
        cloudRevisions.current.set(item.id,item.revision);
        restored.push({ ...applicationFor(item.id,journey), updated:'Cloud-saved preparation' });
      }
      setApplications(previous => {
        const changedDuringLoad = localEditGeneration.current !== generationAtStart;
        const localById = new Map(previous.map(item => [item.id,item]));
        for (const remote of restored) {
          const local = localById.get(remote.id);
          if (!local || !changedDuringLoad) localById.set(remote.id,remote);
        }
        return [...localById.values()];
      });
      if (restored.length>0 && !workspaceTouched.current) {
        const latest=records.find(item=>restored.some(a=>a.id===item.id));
        if(latest){activateCloudId(latest.id);hydrateWorkspace(latest);lastSyncPayload.current=JSON.stringify({planner_state:latest.planner_state??{},household_state:latest.household_state??{},assessment_history:latest.assessment_history??[]});}
      }
      if (invalidRecords > 0) {
        setCloudRestoreFailed(true);
        setStorageNotice(`Cloud returned ${invalidRecords} incompatible preparation(s); no records were deleted. Try reopening by record ID.`);
      } else {
        setCloudRestoreFailed(false);
        setStorageNotice(`Cloud preparations restored (${restored.length}). Document files remain browser-local.`);
      }
    }).catch(() => {
      if (!canceled) {
        setCloudRestoreFailed(true);
        setStorageNotice('Cloud restore is temporarily unavailable. Existing browser/session preparations were not deleted.');
      }
    }).finally(() => {
      if (!canceled) setCloudRestoring(false);
    });
    return () => { canceled = true; };
  }, [activateCloudId, hydrateWorkspace]);
  useEffect(()=>{
    if(!preparationSaving)return;
    persistPreparations(PREPARATION_KEY,JSON.stringify({schemaVersion:1,records:applications.filter(a=>a.journey)}));
  },[applications,preparationSaving]);
  function setPreparationSaving(enabled:boolean) {
    try {
      if(enabled){localStorage.setItem(PREPARATION_CONSENT,'yes');localStorage.setItem(PREPARATION_KEY,JSON.stringify({schemaVersion:1,records:applications.filter(a=>a.journey)}));}
      else {localStorage.removeItem(PREPARATION_CONSENT);localStorage.removeItem(PREPARATION_KEY);}
      clearPersistenceFailure();
      setSaving(enabled);setStorageNotice(enabled?'Browser-local saving enabled for preparations. Files have separate Vault controls.':'Browser-local preparation copies deleted. Current preparations remain in this session.');
    } catch {setStorageNotice('Could not change local storage. Check browser permissions.');}
  }
  const updatePreparation = useCallback((id:string,patch:Partial<JourneyData>) => {
    localEditGeneration.current += 1;
    setApplications(old=>old.map(a=>{if(a.id!==id||!a.journey)return a;const data=readJourney({...a.journey,...patch});return data?applicationFor(id,data):a;}));
  }, []);
  // Fetch a specific record by ID when list hydration was unavailable, delayed,
  // truncated or rejected it. Never create a replacement with a new ID.
  const restorePreparationFromCloud = useCallback(async (id:string):Promise<boolean> => {
    if (!/^LOCAL-[A-Za-z0-9-]{8,100}$/.test(id)) return false;
    try {
      const item = await cloudApplications.get(id);
      const journey = cloudToPreparation(item);
      if (!journey || item.id !== id) {
        setCloudRestoreFailed(true);
        setStorageNotice('The cloud preparation format is incompatible. Original cloud data was not changed.');
        return false;
      }
      cloudRevisions.current.set(id,item.revision);
      activateCloudId(id);
      hydrateWorkspace(item);
      lastSyncPayload.current=JSON.stringify({planner_state:item.planner_state??{},household_state:item.household_state??{},assessment_history:item.assessment_history??[]});
      setApplications(previous => {
        // Never overwrite a preparation already edited in this session.
        if (previous.some(a => a.id === id && a.journey)) return previous;
        return [{...applicationFor(id,journey),updated:'Cloud-saved preparation'},...previous];
      });
      setCloudRestoreFailed(false);
      setStorageNotice('Cloud preparation restored. Document files remain browser-local.');
      return true;
    } catch (error) {
      setCloudRestoreFailed(true);
      const unavailable = error instanceof Error && 'status' in error && error.status === 404;
      setStorageNotice(unavailable
        ? 'No preparation was found under this anonymous Firebase account. Check the browser profile and localhost address.'
        : 'Cloud preparation could not be retrieved. No replacement was created; retry when connected.');
      return false;
    }
  }, [activateCloudId, hydrateWorkspace]);
  const activateSavedPreparation = useCallback(async (id:string):Promise<void> => {
    // Only trusted IDs already listed for this Firebase UID can be activated.
    if(activeCloudId.current===id || !cloudRevisions.current.has(id))return;
    if(activeCloudSaves.current.size>0)return;
    try{
      const item=await cloudApplications.get(id);
      if(item.id!==id || !cloudToPreparation(item))return;
      activateCloudId(id);
      cloudRevisions.current.set(id,item.revision);
      workspaceTouched.current=false;
      hydrateWorkspace(item);
      lastSyncPayload.current=JSON.stringify({planner_state:item.planner_state??{},household_state:item.household_state??{},assessment_history:item.assessment_history??[]});
    }catch{setStorageNotice('Unable to load planner/household progress for this preparation. Existing local edits are intact.');}
  }, [activateCloudId, hydrateWorkspace]);
  function deletePreparation(id:string){
    const revision = cloudRevisions.current.get(id);
    const deleteLocal = () => {
      localEditGeneration.current += 1;
      cloudRevisions.current.delete(id);
      if(activeCloudId.current===id){activateCloudId(null);lastSyncPayload.current='';}
      setApplications(old=>old.filter(a=>a.id!==id||!a.journey));
    };
    if (revision === undefined) { deleteLocal(); return; }
    if (activeCloudSaves.current.has(id)) {
      setStorageNotice('Cloud save is in progress. Please retry deleting after it completes.');
      return;
    }
    cloudApplications.remove(id,revision)
      .then(() => { deleteLocal(); setStorageNotice('Cloud preparation deleted. Browser-local files remain controlled separately.'); })
      .catch(() => setStorageNotice('Could not delete the cloud preparation; record retained. Please retry.'));
  }

  async function savePreparationToCloud(id:string,patch:Partial<JourneyData>):Promise<string> {
    const application = applicationsRef.current.find(a=>a.id===id && a.journey);
    const journey = application?.journey && readJourney({...application.journey,...patch});
    if (!journey || !application) return 'This preparation could not be validated. Cloud save was not attempted.';
    updatePreparation(id,patch); // local session state always works, independent of cloud availability
    if (cloudRestoring) return 'Cloud restoration is still running; retry saving in a moment.';
    if (activeCloudSaves.current.has(id)) return 'Cloud save is already running. Wait and retry.';
    if (!cloudConsent.current || (()=>{try{return localStorage.getItem(CLOUD_WORKSPACE_CONSENT_KEY)!=='yes';}catch{return true;}})()) {
      const approved = window.confirm(
        'Save this preparation to Google Cloud Firestore? Your applicant details, answers, selected document IDs, planner progress and household member labels/dependency links will be stored under your anonymous Firebase identity. Document files stay in this browser. Use fictional information in the public demo. This is not a government submission. Continue?'
      );
      if (!approved) return 'Cloud saving declined. Preparation remains in this browser session (and locally if enabled).';
    }
    activeCloudSaves.current.add(id);
    try {
      const payload = {...preparationToCloud(id,journey),...workspacePayload()};
      const knownRevision = cloudRevisions.current.get(id);
      let stored;
      if (knownRevision !== undefined) {
        const {client_id: _clientId,service_type: _serviceType,...changes} = payload;
        void _clientId; void _serviceType;
        stored = await cloudApplications.update(id,{...changes,revision:knownRevision});
      } else {
        stored = await cloudApplications.create(payload);
        if (!sameCloudPreparation(stored,payload)) {
          return 'A different cloud version already exists. Cloud changes were not overwritten; reload and review it before saving.';
        }
      }
      const confirmedJourney=cloudToPreparation(stored);
      if(!confirmedJourney || stored.id!==id || !sameCloudPreparation(stored,payload))throw new Error('Cloud acknowledgment did not match the saved preparation');
      // Merge only timestamps; edits made while awaiting acknowledgment remain local.
      setApplications(previous=>previous.map(a=>a.id===id&&a.journey?applicationFor(id,{...a.journey,createdAt:confirmedJourney.createdAt,lastSavedAt:confirmedJourney.lastSavedAt}):a));
      cloudRevisions.current.set(id,stored.revision);
      activateCloudId(id);
      lastSyncPayload.current=JSON.stringify(workspacePayload());
      cloudSyncBlocked.current=false;
      cloudConsent.current = true;
      try {localStorage.setItem(CLOUD_CONSENT_KEY,'yes');localStorage.setItem(CLOUD_WORKSPACE_CONSENT_KEY,'yes');}
      catch {setStorageNotice('Cloud save succeeded, but browser storage is blocked. Cloud preparations may not automatically restore after reload.');}
      setStorageNotice('Cloud preparation saved successfully. Actual document files are still browser-local.');
      return 'Saved to Maadhyam cloud (Firestore). Reopen through My Preparations after a refresh.';
    } catch (error) {
      const conflict = error instanceof Error && 'status' in error && error.status === 409;
      const message = conflict
        ? 'Cloud revision conflict; reload the saved preparation before retrying. Local state was preserved.'
        : 'Cloud save failed. Your browser/session preparation remains available; retry when connected.';
      setStorageNotice(message);
      return message;
    } finally { activeCloudSaves.current.delete(id); }
  }
  async function saveHouseholdToCloud():Promise<string> {
    const id=activeCloudId.current;
    if(!id)
      return 'Open an existing cloud-saved Passport preparation first. Household changes remain local.';

    const revision=cloudRevisions.current.get(id);
    if(revision===undefined)
      return 'This preparation is not ready for cloud synchronization. Open its saved journey first.';

    if(cloudRestoring || activeCloudSaves.current.has(id))
      return 'Cloud synchronization is in progress. Please retry.';

    const approved=window.confirm(
      `Save household member labels and dependency references to Google Cloud `+
      `under preparation ${id}? This does not upload document files, verify `+
      `relationships or submit anything to the government. Use fictional data. Continue?`
    );
    if(!approved)
      return 'Household cloud save declined. Local state remains unchanged.';

    activeCloudSaves.current.add(id);
    try {
      const payload=workspacePayload();
      const saved=await cloudApplications.update(id,{
        revision,
        ...payload,
      });
      cloudRevisions.current.set(id,saved.revision);
      setApplications(previous=>previous.map(a=>a.id===id&&a.journey?applicationFor(id,{...a.journey,lastSavedAt:saved.lastSavedAt??saved.updated_at}):a));
      lastSyncPayload.current=JSON.stringify(payload);
      cloudSyncBlocked.current=false;
      cloudConsent.current=true;

      try {
        localStorage.setItem(CLOUD_CONSENT_KEY,'yes');
        localStorage.setItem(CLOUD_WORKSPACE_CONSENT_KEY,'yes');
      } catch {
        setStorageNotice('Cloud save succeeded; browser storage is unavailable.');
      }

      return `Household snapshot saved to Firestore under ${id}.`;
    } catch(error) {
      if(error instanceof Error && 'status' in error && error.status===409)
        return 'Cloud revision conflict. Reopen the preparation and retry. No cloud data was overwritten.';
      return 'Household cloud save failed. Changes remain in this browser session.';
    } finally {
      activeCloudSaves.current.delete(id);
    }
  }

  // After explicit cloud-workspace consent, persist planner/household edits behind a
  // short debounce; never send document bytes or silently overwrite on revision conflict.
  const workspacePayloadJSON = JSON.stringify({
    manual_task_ids:manuallyCompleted,
    target_date:plannerTargetDate,
    plan:plannerSnapshot,
    household:members,
  });
  useEffect(()=>{
    const id=activeCloudId.current;
    if(!id || cloudSyncBlocked.current || !cloudConsent.current || cloudRestoring)return;
    try{if(localStorage.getItem(CLOUD_WORKSPACE_CONSENT_KEY)!=='yes')return;}catch{return;}
    const values=JSON.stringify(workspacePayload());
    if(values===lastSyncPayload.current)return;
    const handle=setTimeout(()=>{
      if(activeCloudSaves.current.has(id))return;
      const revision=cloudRevisions.current.get(id);
      if(revision===undefined)return;
      activeCloudSaves.current.add(id);
      const payload=workspacePayload();
      cloudApplications.update(id,{revision,...payload})
        .then(saved=>{
          cloudRevisions.current.set(id,saved.revision);
          setApplications(previous=>previous.map(a=>a.id===id&&a.journey?applicationFor(id,{...a.journey,lastSavedAt:saved.lastSavedAt??saved.updated_at}):a));
          lastSyncPayload.current=JSON.stringify(payload);
          setHistory(payload.assessment_history);
        })
        .catch(error=>{
          if(error instanceof Error && 'status' in error && error.status===409){
            cloudSyncBlocked.current=true;
            setStorageNotice('Planner/household cloud revision changed. Reload the preparation to review before resaving.');
          }else{
            setStorageNotice('Planner/household cloud sync failed; changes remain in this session. Retry after checking the connection.');
          }
        })
        .finally(()=>activeCloudSaves.current.delete(id));
    },1200);
    return()=>clearTimeout(handle);
  },[workspacePayloadJSON,cloudRestoring,workspacePayload,activeCloudPreparationId]);
  const { documents } = useDocuments();
  // Only objective Vault actions are inferred; reviewing a discrepancy or official
  // requirement must be explicitly acknowledged by the citizen.
  const plannerCompleted = useMemo(() => {
    const done = new Set(manuallyCompleted);
    if (documents.length > 0 && done.has("journey")) done.add("vault");
    if (done.has("vault") && documents.some(d => d.status === "reviewed" && d.metadata.holder === "self")) {
      done.add("details");
    }
    return plannerTasks.filter(t => done.has(t.id)).map(t => t.id);
  }, [documents, manuallyCompleted]);
  const liveSteps = plannerTasks.map(t => t.title);
  const liveDone = plannerCompleted.length;
  const liveNext = plannerTasks.find(t => !plannerCompleted.includes(t.id));
  const livePreparation: Application = {
    id: "VAULT-PREPARATION",
    service: "Passport",
    type: "Your current document preparation",
    status: liveDone === 0 ? "draft" : liveDone === plannerTasks.length ? "completed" : "in-progress",
    completedSteps: liveDone,
    totalSteps: plannerTasks.length,
    nextAction: liveNext?.title ?? "Review current official Passport Seva instructions",
    updated: "Live from this browser session",
    steps: liveSteps,
  };
  const visibleApplications = [livePreparation, ...applications];
  function createDraft(type:PassportAssistanceType='fresh') {
    const id = `LOCAL-${crypto.randomUUID()}`;
    localEditGeneration.current += 1;
    setApplications(previous=>[applicationFor(id,{...newJourney(type),createdAt:new Date().toISOString(),documentIds:documents.map(d=>d.id)}),...previous]);
    return id;
  }
  function togglePlannerTask(id: string) {
    workspaceTouched.current=true;
    setManuallyCompleted((previous) => {
      const completed = new Set(plannerCompleted);
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
  function changePlannerTargetDate(value:string){workspaceTouched.current=true;setPlannerTargetDate(value);}
  return <WorkspaceContext.Provider value={{ applications: visibleApplications, createDraft, updatePreparation, preparationSaving, storageNotice:localPersistenceFailure || storageNotice, setPreparationSaving, deletePreparation, savePreparationToCloud, cloudRestoring, cloudRestoreFailed, restorePreparationFromCloud, activateSavedPreparation, activeCloudPreparationId, saveHouseholdToCloud, plannerCompleted, togglePlannerTask, resetPlanner: () => {workspaceTouched.current=true;setManuallyCompleted([]);}, plannerTargetDate, setPlannerTargetDate:changePlannerTargetDate, recordPlannerAnalysis }}>{children}</WorkspaceContext.Provider>;
}
