
import { getFirebaseToken } from "./firebaseClient";

const configuredBase =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)
    ?.replace(/\/+$/, "") ?? "";

const API_BASE =
  configuredBase ||
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

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
  revision: number;
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
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "CloudApplicationError";
  }
}

async function apiRequest<T>(
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
