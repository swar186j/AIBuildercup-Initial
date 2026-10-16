// Validate render-critical fields at the API boundary. Type assertions alone
// cannot protect React from a truncated or unexpected successful response.
type RecordValue = Record<string, unknown>;
function object(value: unknown): value is RecordValue {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(item => typeof item === 'string');
}
function records(value: unknown, valid: (item: RecordValue) => boolean): boolean {
  return Array.isArray(value) && value.every(item => object(item) && valid(item));
}
function tasks(value: unknown): boolean {
  return records(value, item => typeof item.id === 'string' && typeof item.title === 'string' && strings(item.dependsOn));
}
function assessment(value: unknown): boolean {
  return object(value) && tasks(value.tasks) && strings(value.familyHolders) &&
    records(value.findings, item => typeof item.id === 'string' && typeof item.field === 'string' && typeof item.message === 'string');
}
export function validatePassportPlan(value: unknown): void {
  if (!object(value) || !assessment(value.assessment) || !object(value.passportPlan) ||
    !strings(value.passportPlan.orderedTaskIds) || !strings(value.passportPlan.preparationBlockers) ||
    !records(value.passportPlan.resolutionOptions, item => typeof item.findingId === 'string' && records(item.alternatives, alt => typeof alt.id === 'string' && typeof alt.label === 'string'))) {
    throw new Error('Unexpected Passport planning response. Please retry.');
  }
}
export function validateReasoning(value: unknown): void {
  if (!object(value) || !object(value.baseline) || !assessment(value.baseline.assessment) ||
    !object(value.dependencyGraph) || !strings(value.dependencyGraph.executionOrder) ||
    !records(value.dependencyGraph.nodes, item => typeof item.id === 'string' && typeof item.title === 'string') ||
    !records(value.dependencyGraph.edges, item => typeof item.before === 'string' && typeof item.after === 'string') ||
    !object(value.familyEvidence) || !records(value.familyEvidence.links, item => typeof item.documentId === 'string' && strings(item.reviewedRelationshipEvidenceIds)) ||
    !records(value.simulations, item => typeof item.id === 'string' && strings(item.resolvedFindingIds) && strings(item.newFindingIds) &&
      object(item.before) && strings(item.before.reviewFindings) && strings(item.before.blockers) &&
      object(item.after) && strings(item.after.reviewFindings) && strings(item.after.blockers))) {
    throw new Error('Unexpected document reasoning response. Please retry.');
  }
  const path = value.minimumCorrectionPath;
  const deadlock = value.deadlockAnalysis;
  const proof = value.proofSubstitution;
  const identity = value.identityEvolution;
  const address = value.addressContinuity;
  const visit = value.visitPreparation;
  const deadline = value.deadlineRescue;
  if (!object(path) || !strings(path.selectedTaskIds) || typeof path.selectedTaskCount !== 'number' || typeof path.totalTaskCount!=='number'||typeof path.optimizationScope!=='string'||
    !object(deadlock) || typeof deadlock.note!=='string'||!records(deadlock.issues, item => strings(item.taskIds) && typeof item.message === 'string') ||
    !object(proof) || !records(proof.candidates, item => typeof item.category === 'string' && strings(item.candidateDocumentIds)) ||
    !object(identity) || (identity.nextAction!==undefined&&typeof identity.nextAction!=='string')||typeof identity.note!=='string'||!records(identity.observedNameVariants, item => typeof item.name === 'string' && strings(item.documentIds)) ||
    !object(address) || (address.nextAction!==undefined&&typeof address.nextAction!=='string')||typeof address.note!=='string'||!records(address.observedAddresses, item => typeof item.address === 'string' && strings(item.documentIds)) ||
    !object(visit) || typeof visit.note!=='string'||!strings(visit.actions) ||
    !object(deadline) || typeof deadline.urgency !== 'string' || !strings(deadline.actions) || (deadline.documentExpiryConflicts!==undefined&&!records(deadline.documentExpiryConflicts,c=>typeof c.documentId==='string'&&typeof c.expiryDate==='string'&&typeof c.type==='string'&&typeof c.action==='string'&&(c.message===undefined||typeof c.message==='string')))) {
    throw new Error('Unexpected advanced planning response. Please retry.');
  }
}
export function validateChat(value: unknown): void {
  if (!object(value) || typeof value.answer !== 'string' || !value.answer.trim()) {
    throw new Error('The assistant returned an empty or unexpected response.');
  }
}

export function validatePassportAssessment(value:unknown):void {
  if(!object(value)||typeof value.ruleset_version!=='string'||typeof value.official_requirements_verified!=='boolean'||typeof value.source_health!=='string'||typeof value.disclaimer!=='string'||!records(value.checks,c=>typeof c.id==='string'&&typeof c.title==='string'&&['available-for-review','needs-attention','needs-confirmation'].includes(String(c.status))&&typeof c.reason==='string'&&typeof c.next_action==='string'&&strings(c.alternatives)&&strings(c.matching_document_ids)&&typeof c.source_url==='string'&&(c.source_url===''||c.source_url.startsWith('https://'))&&typeof c.source_id==='string'))throw new Error('Unexpected Passport assessment response. Please retry.');
}
