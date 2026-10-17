import {serializeWorkspace} from '../utils/workspaceSnapshot';
import {trackCloudSave} from './saveNotifications';

import { getFirebaseToken } from "./firebaseClient";

const configuredBase =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)
    ?.replace(/\/+$/, "") ?? "";

const API_BASE =
  configuredBase ||
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

export type PlannerCloudState = {
  manual_task_ids: string[];
  target_date: string | null;
  generated_plan: Record<string, unknown>;
};
export type HouseholdCloudMember = {
  createdAt?:string;
  updatedAt?:string;
  id: string;
  label: string;
  relationship: 'self' | 'parent' | 'guardian' | 'spouse' | 'child' | 'sibling' | 'other';
  dependsOnMemberIds: string[];
  dependsOnDocumentIds: string[];
  relationshipEvidenceDocumentIds: string[];
};
export type HouseholdCloudState = { members: HouseholdCloudMember[] };
export type AssessmentCloudEntry = {
  captured_at: string;
  task_count: number;
  finding_count: number;
  task_ids: string[];
  assessment_id: string;
  input_document_ids: string[];
  source_url: string;
  rule_pack_version: string;
  status: 'prepared' | 'needs-review' | 'failed';
};

export type CloudApplication = {
  id: string;
  service_type: string;
  application_type: string;
  status: "draft" | "in-progress" | "completed";
  applicant_details: Record<string, unknown>;
  questionnaire_answers: Record<string, unknown>;
  current_step: number;
  selected_document_ids: string[];
  rule_pack_version: string;
  planner_state?: PlannerCloudState;
  household_state?: HouseholdCloudState;
  assessment_history?: AssessmentCloudEntry[];
  revision: number;
  lastSavedAt?: string;
  created_at: string;
  updated_at: string;
};

export type CreateCloudApplication = {
  client_id?: string;
  service_type?: string;
  application_type?: string;
  status?: CloudApplication["status"];
  applicant_details?: Record<string, unknown>;
  questionnaire_answers?: Record<string, unknown>;
  current_step?: number;
  selected_document_ids?: string[];
  rule_pack_version?: string;
  planner_state?: PlannerCloudState;
  household_state?: HouseholdCloudState;
  assessment_history?: AssessmentCloudEntry[];
};

export type UpdateCloudApplication = Partial<
  Omit<
    CreateCloudApplication,
    "client_id" | "service_type"
  >
> & {
  revision: number;
};

export class CloudApplicationError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "CloudApplicationError";
    this.status = status;
  }
}

async function performRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = await getFirebaseToken();

  const response = await fetch(
    `${API_BASE}/api/applications${path}`,
    {
      ...init,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(init.body
          ? { "Content-Type": "application/json" }
          : {}),
      },
      cache: "no-store",
      signal: init.signal ?? AbortSignal.timeout(20000),
    },
  );

  const body = response.status === 204
    ? null
    : await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      body?.error?.message ??
      body?.detail ??
      `Request failed (${response.status})`;

    throw new CloudApplicationError(
      response.status,
      String(message),
    );
  }

  return body as T;
}

async function apiRequest<T>(path:string,init:RequestInit={}):Promise<T>{
 if(!init.method||init.method==='GET')return performRequest<T>(path,init);
 const label=init.method==='DELETE'?'Application deleted':init.method==='POST'?'Preparation saved':init.body?.toString().includes('questionnaire_answers')?'Preparation saved':init.body?.toString().includes('household_state')?'Planner progress and household saved to cloud':'Application updated';
 return trackCloudSave(`application:${path}`,label,async()=>{
   const result=await performRequest<T>(path,init);
   if(init.method!=='DELETE'){
     const record=result as CloudApplication;
     if(!record||typeof record.id!=='string'||!Number.isInteger(record.revision)||typeof record.updated_at!=='string')throw new Error('Invalid cloud save acknowledgment. Changes remain local.');
     const payload=JSON.parse(String(init.body)) as CreateCloudApplication & {revision?:number};
     if((payload.client_id&&record.id!==payload.client_id)||(path&&record.id!==decodeURIComponent(path.slice(1)))||(payload.revision!==undefined&&record.revision<=payload.revision))throw new Error('Cloud acknowledgment has the wrong preparation or revision.');
     for(const key of ['household_state','planner_state','questionnaire_answers'] as const){if(payload[key]&&serializeWorkspace(payload[key])!==serializeWorkspace(record[key]))throw new Error('Cloud acknowledgment differs from the submitted snapshot. Retry after reviewing the saved preparation.');}
   }
   return result;
 });
}

export const cloudApplications = {
  list() {
    return apiRequest<CloudApplication[]>("");
  },

  get(id: string) {
    return apiRequest<CloudApplication>(
      `/${encodeURIComponent(id)}`,
    );
  },

  create(data: CreateCloudApplication) {
    return apiRequest<CloudApplication>("", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update(id: string, data: UpdateCloudApplication) {
    return apiRequest<CloudApplication>(
      `/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      },
    );
  },

  remove(id: string, revision: number) {
    return apiRequest<void>(
      `/${encodeURIComponent(id)}?revision=${revision}`,
      { method: "DELETE" },
    );
  },
};
