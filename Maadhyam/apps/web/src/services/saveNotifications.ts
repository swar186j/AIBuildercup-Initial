export type SaveNotice={id:string;state:'saving'|'saved'|'failed';message:string};
let notices:SaveNotice[]=[];
const listeners=new Set<()=>void>();
export const subscribeSaveNotices=(listener:()=>void)=>{listeners.add(listener);return()=>{listeners.delete(listener);};};
export const getSaveNotices=()=>notices;
function publish(){listeners.forEach(listener=>listener());}
export function dismissSaveNotice(id:string){notices=notices.filter(n=>n.id!==id);publish();}
export async function trackCloudSave<T>(id:string,success:string,action:()=>Promise<T>,incomplete?:(value:T)=>boolean):Promise<T>{
 const update=(state:SaveNotice['state'],message:string)=>{notices=[...notices.filter(n=>n.id!==id),{id,state,message}];publish();};
 update('saving','Saving to cloud…');
 try{const value=await action();if(incomplete?.(value)){update('failed',success+' incomplete. Some items failed; retry from the affected module.');return value;}update('saved',success);const confirmed=notices.find(n=>n.id===id);setTimeout(()=>{if(notices.find(n=>n.id===id)===confirmed)dismissSaveNotice(id);},6000);return value;}
 catch(error){update('failed',`${success.replace(/saved|updated|deleted|migrated/gi,'save')} failed. ${error instanceof Error?error.message:'Please retry from the affected item.'}`);throw error;}
}
