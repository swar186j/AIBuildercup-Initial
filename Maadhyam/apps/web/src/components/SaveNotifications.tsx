import {useSyncExternalStore} from 'react';
import {dismissSaveNotice,getSaveNotices,subscribeSaveNotices} from '../services/saveNotifications';
export default function SaveNotifications(){
 const notices=useSyncExternalStore(subscribeSaveNotices,getSaveNotices,getSaveNotices);
 return <aside aria-label="Cloud save notifications" className="fixed left-3 top-3 z-50 max-h-[45vh] w-[calc(100%-1.5rem)] max-w-sm space-y-2 overflow-auto sm:left-auto sm:right-4">{notices.map(n=><div key={n.id} role={n.state==='failed'?'alert':'status'} className={`rounded-xl border bg-white p-3 text-sm shadow-lg dark:bg-slate-900 ${n.state==='failed'?'border-red-400 text-red-800 dark:text-red-200':'border-teal-500 text-teal-900 dark:text-teal-100'}`}><span>{n.message}</span>{n.state!=='saving'&&<button type="button" onClick={()=>dismissSaveNotice(n.id)} aria-label={`Dismiss ${n.message}`} className="ml-3 underline">Dismiss</button>}</div>)}</aside>;
}
