import type { Application } from './WorkspaceContext';

export function isEmptyPreparation(app: Application): boolean {
  const journey = app.journey;
  return Boolean(journey && app.status === 'draft' && journey.stepIndex === 0
    && !journey.applicantName.trim() && !journey.applicantDob
    && Object.entries(journey.answers).every(([key, value]) => key === 'assistanceType' || value === ''));
}

/** Keep filled records prominent; unfilled drafts remain accessible without deletion. */
export function groupEmptyPreparations(applications: Application[]) {
  const visible: Application[] = [];
  const olderEmpty: Application[] = [];
  for (const app of applications) {
    if (!isEmptyPreparation(app)) { visible.push(app); continue; }
    olderEmpty.push(app);
  }
  return { visible, olderEmpty };
}
