import { authenticatedFetch } from './authenticatedApi';
export type ExtractionResult = {
  documentType: string | null;
  printedName: string | null;
  dateOfBirth: string | null;
  residentialAddress: string | null;
  categories: Array<"identity" | "address" | "birth" | "education" | "employment" | "other">;
  warnings: string[];
};

export async function extractDocument(file: File, signal?: AbortSignal): Promise<ExtractionResult> {
  const form = new FormData();
  form.append("file", file, file.name);
  form.append("fictional_document_confirmed", "true");
  const deadline = AbortSignal.timeout(50000);
  const requestSignal = signal ? AbortSignal.any([signal, deadline]) : deadline;
  let response: Response;
  try {
    response = await authenticatedFetch("/api/ai/extract-document", { method: "POST", body: form, signal: requestSignal });
  } catch (error) {
    if (signal?.aborted) throw error;
    if (deadline.aborted) throw new Error("Extraction timed out. Retry or enter the fictional details manually.", { cause: error });
    throw new Error("Could not connect to the extraction service. Check that FastAPI is running.", { cause: error });
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const payload = body as { error?: { message?: string }; detail?: string } | null;
    throw new Error(payload?.error?.message || payload?.detail || `Extraction failed (${response.status})`);
  }
  const result = body as ExtractionResult;
  if (!result || !Array.isArray(result.categories) || !Array.isArray(result.warnings)) {
    throw new Error("Unexpected extraction response from the server.");
  }
  return result;
}
