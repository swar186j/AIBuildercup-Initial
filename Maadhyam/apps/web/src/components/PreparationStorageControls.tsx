import { useWorkspace } from '../context/WorkspaceContext';
export default function PreparationStorageControls() {
  const { cloudReady, cloudBusy, cloudLoading, cloudSaving, retryCloud, storageNotice } = useWorkspace();
  return <section aria-label="Preparation storage controls" className="rounded-2xl border border-slate-200 bg-white p-5 text-sm dark:bg-slate-900">
    <h2 className="font-semibold">Your account storage</h2>
    <p className="mt-2">Preparation answers and progress are saved privately to your account.</p>
    <p role="status" className="mt-2">{cloudBusy || cloudSaving ? 'Saving changes…' : storageNotice}</p>
    {!cloudReady && !cloudLoading && <button type="button" onClick={retryCloud} className="mt-3 rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white">Retry connection</button>}
  </section>;
}
