// No test-only behavior is added to the app. Transpile its real API client and
// substitute only the transport to exercise failures deterministically.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'Maadhyam/apps/web/node_modules/typescript'));
const filename = path.join(root, 'Maadhyam/apps/web/src/services/m10Applications.ts');
let source = fs.readFileSync(filename, 'utf8').replace(
  "import { authenticatedFetch } from './authenticatedApi';",
  'const authenticatedFetch = (...args: any[]) => (globalThis as any).mockFetch(...args);',
);
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const result = { exports: {} };
new Function('exports', 'module', compiled)(result.exports, result);
const api = result.exports;

(async () => {
  globalThis.mockFetch = async () => new Response(JSON.stringify([]), { status: 200 });
  assert.deepEqual(await api.listCloudApplications(), []);
  globalThis.mockFetch = async () => new Response(null, { status: 204 });
  assert.equal(await api.deleteCloudApplication('LOCAL-fictional-123', 1), undefined);
  globalThis.mockFetch = async () => new Response(JSON.stringify({ error: { message: 'Revision conflict' } }), { status: 409 });
  await assert.rejects(api.listCloudApplications(), error => error.status === 409 && error.message === 'Revision conflict');
  globalThis.mockFetch = async () => { throw new Error('Synthetic network outage'); };
  await assert.rejects(api.listCloudApplications(), /connection unavailable/);
  const realTimeout = globalThis.setTimeout;
  try {
    globalThis.setTimeout = callback => realTimeout(callback, 10);
    globalThis.mockFetch = () => new Promise(() => {});
    await assert.rejects(api.listCloudApplications(), /timed out/);
    globalThis.mockFetch = async () => new Response(new ReadableStream({ start() {} }), { status: 200 });
    await assert.rejects(api.listCloudApplications(), /timed out/);
  } finally {
    globalThis.setTimeout = realTimeout;
    delete globalThis.mockFetch;
  }
  console.log('6 API client checks passed: JSON, deletion, conflict, network failure, request timeout, body timeout');
})().catch(error => { console.error(error); process.exitCode = 1; });
