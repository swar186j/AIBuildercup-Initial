export function friendlyLabel(key:string):string {
 const labels:Record<string,string>={dateOfBirth:'Date of Birth',residentialAddress:'Residential Address',printedName:'Name on Document','possible-initial-expansion':'Possible Name Variation',extractionConfidence:'Extraction confidence'};
 return labels[key]??key.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/[-_]/g,' ').replace(/^./,c=>c.toUpperCase());
}
