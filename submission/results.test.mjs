import assert from 'node:assert/strict';
import test from 'node:test';
import { validateResults } from './results.mjs';

// Contract-only invented values. These are never saved as final Run results.
function retainedResults() {
  return {
    benchmark_approved: true, frozen_commit: 'a'.repeat(40), model: 'test-model',
    run_ids: ['test-run'], artifacts: ['test-artifact.json'],
    planned_cases: 10, scored_cases: 1, attempts: 2, cost_usd: null,
    aggregate: { tp: 1, fp: 0, fn: 1, precision: 1, recall: 0.5, f1: 2 / 3,
      quote_provenance_accuracy: 1, source_attribution_accuracy: null },
    cases: [
      { id: 'heldout_01', status: 'scored', precision: 1, recall: 0.5, f1: 2 / 3 },
      { id: 'heldout_02', status: 'failed', precision: null, recall: null, f1: null },
      ...Array.from({ length: 8 }, (_, index) => ({
        id: `heldout_${String(index + 3).padStart(2, '0')}`, status: 'unscored',
        precision: null, recall: null, f1: null,
      })),
    ],
    failures: [{ case_id: 'heldout_02', stage: 'extract', description: 'Test provider failure' }],
  };
}

test('accepts retained mixed scored and failed coverage without changing input', () => {
  const value = retainedResults();
  const before = structuredClone(value);
  assert.doesNotThrow(() => validateResults(value));
  assert.deepEqual(value, before);
});

test('rejects a final export with only two held-out cases', () => {
  const value = retainedResults();
  value.planned_cases = 2;
  value.cases = value.cases.slice(0, 2);
  assert.throws(() => validateResults(value), /Case coverage/);
});

test('rejects a failed case carrying scored metrics', () => {
  const value = retainedResults();
  value.cases[1].f1 = 0.5;
  assert.throws(() => validateResults(value), /Unscored case/);
});

test('rejects coverage inconsistent with per-case status', () => {
  const value = retainedResults();
  value.scored_cases = 2;
  assert.throws(() => validateResults(value), /Scored coverage/);
});

for (const [name, edit] of [
  ['duplicate case identity', value => { value.cases[1].id = 'heldout_01'; }],
  ['unknown case identity', value => { value.cases[1].id = 'heldout_99'; }],
  ['unknown status', value => { value.cases[1].status = 'success'; }],
  ['scored case missing metrics', value => { delete value.cases[0].recall; }],
]) {
  test(`rejects ${name}`, () => {
    const value = retainedResults();
    edit(value);
    assert.throws(() => validateResults(value));
  });
}

for (const attempts of [-1, 1.5, 31, 0, '2', null]) {
  test(`rejects invalid attempt count ${JSON.stringify(attempts)}`, () => {
    const value = retainedResults();
    value.attempts = attempts;
    assert.throws(() => validateResults(value), /attempt/);
  });
}

for (const [name, edit] of [
  ['unknown failure case', value => { value.failures[0].case_id = 'heldout_99'; }],
  ['empty failure stage', value => { value.failures[0].stage = ''; }],
  ['missing failure description', value => { delete value.failures[0].description; }],
  ['unidentified failed case', value => { value.failures = []; }],
  ['duplicate failure identity', value => { value.failures.push({ ...value.failures[0] }); }],
  ['duplicate Run identity', value => { value.run_ids.push('test-run'); }],
  ['blank Run identity', value => { value.run_ids = [' ']; }],
  ['nonarray Run identity', value => { value.run_ids = 'test-run'; }],
]) {
  test(`rejects ${name}`, () => {
    const value = retainedResults();
    edit(value);
    assert.throws(() => validateResults(value));
  });
}

for (const [name, edit] of [
  ['truthy approval instead of true', value => { value.benchmark_approved = 'yes'; }],
  ['blank frozen commit', value => { value.frozen_commit = ' '; }],
  ['negative aggregate count', value => { value.aggregate.tp = -1; }],
  ['fractional aggregate count', value => { value.aggregate.fn = 0.5; }],
  ['negative cost', value => { value.cost_usd = -0.01; }],
  ['out-of-range aggregate metric', value => { value.aggregate.source_attribution_accuracy = 1.1; }],
  ['missing case outcomes', value => { value.cases.pop(); }],
]) {
  test(`rejects ${name}`, () => {
    const value = retainedResults();
    edit(value);
    assert.throws(() => validateResults(value));
  });
}

test('accepts explicit unscored cases and retry attempts without requiring exhaustive scoring', () => {
  const value = retainedResults();
  value.cases[1].status = 'unscored';
  value.attempts = 3;
  value.cost_usd = 0.001;
  assert.doesNotThrow(() => validateResults(value));
});
