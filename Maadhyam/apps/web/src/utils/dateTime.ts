/** Persist UTC; format in the viewer's timezone. Legacy values remain absent. */
export function formatDateTime(value:unknown):string {
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T/.test(value))return 'Not recorded';
 const date=new Date(value);
 if(!Number.isFinite(date.getTime()))return 'Not recorded';
 const parts=new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:true}).formatToParts(date);
 const part=(key:Intl.DateTimeFormatPartTypes)=>parts.find(p=>p.type===key)?.value??'';
 return `${part('day')} ${part('month')} ${part('year')}, ${part('hour')}:${part('minute')} ${part('dayPeriod').toUpperCase()}`;
}
export function validTimestamp(value:unknown):value is string {
 return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}T/.test(value)&&Number.isFinite(Date.parse(value));
}
