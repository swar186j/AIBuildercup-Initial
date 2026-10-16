const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'Maadhyam/apps/web/node_modules/typescript'));
const code = ts.transpileModule(fs.readFileSync(path.join(root, 'Maadhyam/apps/web/src/context/preparationList.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const moduleUnderTest = { exports: {} };
new Function('exports', 'module', code)(moduleUnderTest.exports, moduleUnderTest);
const { groupEmptyPreparations } = moduleUnderTest.exports;
function draft(id, patch = {}) {
  return { id, service: 'Passport', status: 'draft', journey: {
    stepIndex: 0, assistanceType: 'fresh', applicantName: '', applicantDob: '', documentIds: [],
    answers: { assistanceType: 'fresh', applicantAgeGroup: '' }, ...patch,
  } };
}
const records = [draft('newest'), draft('older'), draft('named', { applicantName: 'Fictional Applicant' }),
  draft('answered', { answers: { assistanceType: 'fresh', applicantAgeGroup: 'adult' } }),
  draft('docs', { documentIds: ['different-document'] }), draft('reissue', { assistanceType: 'reissue' })];
const result = groupEmptyPreparations(records);
assert.deepEqual(result.olderEmpty.map(item => item.id), ['newest', 'older', 'docs', 'reissue']);
assert.deepEqual(result.visible.map(item => item.id), ['named', 'answered']);
assert.deepEqual(groupEmptyPreparations([draft('newest'), draft('older')]).visible, []);
assert.deepEqual(groupEmptyPreparations([draft('newest'), draft('older')]).olderEmpty.map(item => item.id), ['newest', 'older']);
assert.equal(records.length, 6); // No deletion or mutation of stored records.
console.log('Grouping checks passed: blank duplicates grouped; names, answers, document selections and types preserved');
