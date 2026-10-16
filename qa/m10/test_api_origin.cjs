const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'Maadhyam/apps/web/node_modules/typescript'));
const source = fs.readFileSync(path.join(root, 'Maadhyam/apps/web/src/services/apiFetch.ts'), 'utf8').replaceAll('import.meta.env', 'globalThis.testEnv');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
function load(env) {
  const mod = {exports:{}};
  const calls = [];
  const scope = {testEnv:env};
  new Function('exports','module','globalThis','fetch', compiled)(mod.exports,mod,scope,(url,init)=>{calls.push({url,init});return Promise.resolve(new Response('{}'));});
  return {api:mod.exports,calls};
}
(async()=>{
  let x=load({DEV:false}); await x.api.apiFetch('/api/services');assert.equal(x.calls[0].url,'/api/services');
  x=load({DEV:false,VITE_API_BASE_URL:'https://fictional-api.onrender.com/'});
  const init={method:'PATCH',headers:{Authorization:'Bearer fictional-token'}};
  await x.api.apiFetch('/api/applications/fictional',init);
  assert.equal(x.calls[0].url,'https://fictional-api.onrender.com/api/applications/fictional');
  assert.equal(x.calls[0].init,init);
  assert.throws(()=>x.api.apiFetch('https://another.example'),/Invalid API path/);
  x=load({DEV:false,VITE_API_BASE_URL:'http://insecure.example'});assert.throws(()=>x.api.apiFetch('/api/services'),/HTTPS/);
  console.log('4 API origin checks passed: same origin, HTTPS deployment origin, headers preserved, insecure/invalid paths rejected');
})().catch(e=>{console.error(e);process.exitCode=1;});
