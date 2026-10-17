import type { DocumentHolder, LocalDocument } from "../context/DocumentContext";

export type ComparedField = "name" | "dateOfBirth" | "address";
export type ComparisonFinding = {
  id: string;
  field: ComparedField;
  holder: DocumentHolder;
  severity: "review";
  title: string;
  explanation: string;
  documents: {
    id: string;
    filename: string;
    value: string;
  }[];
};

export type ComparisonResult = {
  findings: ComparisonFinding[];
  comparedPairs: number;
  comparableFieldPairs: number;
  skippedFieldPairs: number;
  matchedFieldPairs: number;
  excludedDocumentIds: string[];
  comparisons: { field: ComparedField; firstId: string; secondId: string; firstName: string; secondName: string; firstValue: string; secondValue: string; status: "match" | "difference" | "missing"; needsReview: boolean }[];
};

const FIELD_LABELS: Record<ComparedField, string> = {
  name: "Name",
  dateOfBirth: "Date of birth",
  address: "Residential address",
};

function normalizeName(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("en-IN")
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeAddress(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("en-IN")
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeDob(value: string): string {
  // Date input is stored as YYYY-MM-DD; don't infer dates from other formats.
  return value.trim();
}

function getField(document: LocalDocument, field: ComparedField): string {
  switch (field) {
    case "name":
      return document.metadata.printedName?.trim() ?? "";
    case "dateOfBirth":
      return document.metadata.dateOfBirth?.trim() ?? "";
    case "address":
      return document.metadata.residentialAddress?.trim() ?? "";
  }
}

function normalizeField(field: ComparedField, value: string): string {
  switch (field) {
    case "name":
      return normalizeName(value);
    case "dateOfBirth":
      return normalizeDob(value);
    case "address":
      return normalizeAddress(value);
  }
}

const FIELDS: ComparedField[] = ["name", "dateOfBirth", "address"];

/**
 * Compares user-entered metadata only. No OCR, identity verification, or
 * government eligibility assessment occurs here.
 *
 * "holder" is a broad category, not a unique person identifier. Findings
 * must be confirmed by the user before treating records as belonging to
 * the same person (particularly parent-guardian / other categories).
 */
export function comparisonOwner(d: LocalDocument, verifiedMemberIds?: ReadonlySet<string>): string | null {
  if (d.metadata.householdMemberId) return d.metadata.associationConsent === true && (!verifiedMemberIds || verifiedMemberIds.has(d.metadata.householdMemberId)) ? `member:${d.metadata.householdMemberId}` : null;
  // Legacy self means the single applicant in this workspace. Generic categories
  // never identify a person. An explicitly assigned different ID cannot fall back.
  return d.metadata.holder === 'self' ? 'member:applicant' : null;
}
export function compareDocuments(documents: LocalDocument[], verifiedMemberIds?: ReadonlySet<string>): ComparisonResult {
  const findings: ComparisonFinding[] = [];
  let comparedPairs = 0;
  let comparableFieldPairs = 0;
  let skippedFieldPairs = 0;
  let matchedFieldPairs = 0;
  const comparisons: ComparisonResult["comparisons"] = [];

  for (let i = 0; i < documents.length; i += 1) {
    for (let j = i + 1; j < documents.length; j += 1) {
      const first = documents[i];
      const second = documents[j];

      const owner = comparisonOwner(first,verifiedMemberIds);
      if (!owner || owner !== comparisonOwner(second,verifiedMemberIds)) continue;
      comparedPairs += 1;

      for (const field of FIELDS) {
        const firstValue = getField(first, field);
        const secondValue = getField(second, field);

        const status = !firstValue || !secondValue ? "missing" : normalizeField(field, firstValue) === normalizeField(field, secondValue) ? "match" : "difference";
        comparisons.push({ field, firstId: first.id, secondId: second.id, firstName: first.file.name, secondName: second.file.name, firstValue, secondValue, status, needsReview: first.status !== "reviewed" || second.status !== "reviewed" });
        if (!firstValue || !secondValue) {
          skippedFieldPairs += 1;
          continue;
        }

        comparableFieldPairs += 1;
        if (status === "match") {
          matchedFieldPairs += 1;
          continue;
        }

        findings.push({
          id: `${first.id}:${second.id}:${field}`,
          field,
          holder: first.metadata.holder,
          severity: "review",
          title: `Possible ${FIELD_LABELS[field].toLowerCase()} difference`,
          explanation:
            field === "dateOfBirth"
              ? "The reviewed or entered dates differ. Check both documents and confirm the correct date."
              : field === "name"
                ? "The reviewed or entered names differ after basic formatting normalization. Check spelling, initials, and name order."
                : "The reviewed or entered addresses differ after basic formatting normalization. This could reflect an abbreviation, a move, or a genuine discrepancy.",
          documents: [
            { id: first.id, filename: first.file.name, value: firstValue },
            { id: second.id, filename: second.file.name, value: secondValue },
          ],
        });
      }
    }
  }

  return { findings, comparedPairs, comparableFieldPairs, skippedFieldPairs, matchedFieldPairs, comparisons, excludedDocumentIds: documents.filter(d => !comparisonOwner(d,verifiedMemberIds)).map(d => d.id) };
}

export function comparisonSummary(result:ComparisonResult,documents:LocalDocument[],knownIds?:ReadonlySet<string>){
 return {
  confirmedDifferences:result.comparisons.filter(c=>c.status==='difference'&&!c.needsReview).length,
  provisionalDifferences:result.comparisons.filter(c=>c.status==='difference'&&c.needsReview).length,
  confirmedMatches:result.comparisons.filter(c=>c.status==='match'&&!c.needsReview).length,
  missingFields:documents.filter(d=>comparisonOwner(d,knownIds)).reduce((count,d)=>count+FIELDS.filter(field=>!getField(d,field)).length,0),
  unavailableComparisons:result.skippedFieldPairs,
 };
}
