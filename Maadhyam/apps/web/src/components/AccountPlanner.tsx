import { Link } from 'react-router-dom';
import { plannerTasks, useWorkspace } from '../context/WorkspaceContext';

export default function AccountPlanner() {
  const { plannerCompleted, togglePlannerTask, resetPlanner, cloudReady, cloudSaving, storageNotice } = useWorkspace();
  const done = new Set(plannerCompleted);
  return <section aria-label="Saved preparation checklist" className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
    <h2 className="text-xl font-semibold">Your saved preparation checklist</h2>
    <p className="mt-2 text-sm">Mark the steps you have reviewed. Progress is saved to your account and does not confirm official acceptance.</p>
    <ol className="mt-4 space-y-4">
      {plannerTasks.map(task => <li key={task.id} className="flex items-start gap-3">
        <input type="checkbox" aria-label={task.title} checked={done.has(task.id)}
          disabled={!cloudReady || cloudSaving || (!done.has(task.id) && !task.dependsOn.every(id => done.has(id)))}
          onChange={() => togglePlannerTask(task.id)} className="mt-1 h-4 w-4" />
        <div><p className="font-medium">{task.title}</p><p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{task.description}</p>
          <Link to={task.href} className="mt-1 inline-block text-sm text-teal-700 underline dark:text-teal-300">{task.action}</Link></div>
      </li>)}
    </ol>
    <p role="status" className="mt-4 text-sm">{cloudSaving ? 'Saving checklist…' : storageNotice}</p>
    <button type="button" disabled={!cloudReady || cloudSaving || done.size === 0} onClick={resetPlanner} className="mt-3 rounded-lg border px-4 py-2 text-sm disabled:opacity-50">Reset saved checklist</button>
  </section>;
}
