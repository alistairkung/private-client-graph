const relationshipMetrics = ['precision', 'recall', 'f1'];
const aggregateMetrics = [...relationshipMetrics, 'quote_provenance_accuracy', 'source_attribution_accuracy'];
const nonblank = value => typeof value === 'string' && value.trim().length > 0;
const boundedMetric = value => Number.isFinite(value) && value >= 0 && value <= 1;

// Reporting checks only: this neither executes a Run nor grants approval to do so.
export function validateResults(value) {
  if (value?.benchmark_approved !== true) {
    throw new Error('Final export requires explicit benchmark approval and actual retained results.');
  }
  validateLineage(value);
  const caseIds = validateCoverage(value);
  validateFailures(value, caseIds);
  for (const key of aggregateMetrics) {
    if (key === 'source_attribution_accuracy' && value.aggregate?.[key] === null) continue;
    if (!boundedMetric(value.aggregate?.[key])) throw new Error(`Invalid ${key}.`);
  }
  for (const key of ['tp', 'fp', 'fn']) {
    if (!Number.isInteger(value.aggregate?.[key]) || value.aggregate[key] < 0) {
      throw new Error(`Invalid ${key} count.`);
    }
  }
  if (value.cost_usd !== null && (!Number.isFinite(value.cost_usd) || value.cost_usd < 0)) {
    throw new Error('Cost must be a verified USD total or null.');
  }
}

function validateLineage(value) {
  for (const key of ['run_ids', 'artifacts']) {
    const identities = value[key];
    if (!Array.isArray(identities) || identities.length === 0 ||
        !identities.every(nonblank) || new Set(identities).size !== identities.length) {
      throw new Error(`Invalid ${key} identities.`);
    }
  }
  if (![value.frozen_commit, value.model].every(nonblank)) {
    throw new Error('Final results must identify frozen code and model.');
  }
}

function validateCoverage(value) {
  if (value.planned_cases !== 10 ||
      !Number.isInteger(value.scored_cases) || value.scored_cases < 0 ||
      value.scored_cases > value.planned_cases || !Array.isArray(value.cases) ||
      value.cases.length !== value.planned_cases) {
    throw new Error('Case coverage is inconsistent.');
  }
  const caseIds = new Set();
  for (const item of value.cases) {
    if (!item || !/^heldout_(0[1-9]|10)$/.test(item.id) || caseIds.has(item.id)) {
      throw new Error('Case identity must be known and unique.');
    }
    caseIds.add(item.id);
    if (!['scored', 'failed', 'unscored'].includes(item.status)) throw new Error('Invalid case status.');
    if (item.status === 'scored' && !relationshipMetrics.every(key => boundedMetric(item[key]))) {
      throw new Error('Scored cases require bounded metrics.');
    }
    if (item.status !== 'scored' && relationshipMetrics.some(key => item[key] != null)) {
      throw new Error('Unscored case cannot carry scored metrics.');
    }
  }
  if (value.cases.filter(item => item.status === 'scored').length !== value.scored_cases) {
    throw new Error('Scored coverage must match case statuses.');
  }
  const attemptedCases = value.cases.filter(item => item.status !== 'unscored').length;
  if (!Number.isInteger(value.attempts) || value.attempts < attemptedCases || value.attempts > 30) {
    throw new Error('Provider attempts must cover attempted cases and remain within the shared 30-attempt ceiling.');
  }
  return caseIds;
}

function validateFailures(value, caseIds) {
  if (!Array.isArray(value.failures)) throw new Error('Failures must be retained explicitly.');
  const failureIds = new Set();
  const failedCases = new Set();
  for (const failure of value.failures) {
    if (!failure || !caseIds.has(failure.case_id) || !nonblank(failure.stage) || !nonblank(failure.description)) {
      throw new Error('Invalid failure identity or description.');
    }
    const identity = JSON.stringify([failure.case_id, failure.stage]);
    if (failureIds.has(identity)) throw new Error('Duplicate failure identity.');
    failureIds.add(identity);
    failedCases.add(failure.case_id);
  }
  if (value.cases.some(item => item.status === 'failed' && !failedCases.has(item.id))) {
    throw new Error('Failed case requires a retained failure description.');
  }
}
