/** Compare semantic workspace acknowledgments. API serialization can add absent
 * nullable member timestamps and normalize equivalent UTC ISO strings. */
export function serializeWorkspace(value:unknown):string{
 return JSON.stringify(value,(key,item:unknown)=>{
  if(typeof item==='string'&&['createdAt','updatedAt','captured_at'].includes(key)&&/^\d{4}-\d{2}-\d{2}T/.test(item)&&Number.isFinite(Date.parse(item)))return new Date(item).toISOString();
  if(item&&typeof item==='object'&&!Array.isArray(item))return Object.fromEntries(Object.entries(item).filter(([k,v])=>!(['createdAt','updatedAt'].includes(k)&&v==null)).sort(([a],[b])=>a.localeCompare(b)));
  return item;
 });
}
