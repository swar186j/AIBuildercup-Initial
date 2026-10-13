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
  let response: Response;
  try {
    response = await fetch("/api/ai/extract-document", { method: "POST", body: form, signal });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error("Could not connect to the extraction service. Check that FastAPI is running.");
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
