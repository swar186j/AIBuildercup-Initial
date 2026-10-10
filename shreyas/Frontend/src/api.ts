export type Health = {status:string;application:string;version:string};
export async function getHealth():Promise<Health>{
  const response=await fetch('/api/health');
  if(!response.ok) throw new Error(`Backend returned HTTP ${response.status}`);
  return response.json() as Promise<Health>;
}
// Add evidence submission API here after the backend request/response contract is agreed.
