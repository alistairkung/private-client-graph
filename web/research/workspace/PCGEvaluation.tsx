import { useCallback, useState, type ReactNode } from "react";
import { percentMetric } from "../../src/shared/research/presentation";
import type {
  RunDetail, SemanticEvidenceReport, SemanticOperations, SemanticOutcome, SemanticQuotation, SemanticRunSummary, SemanticSummary,
  SemanticTarget, SemanticTransition,
} from "../shared/contracts";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { compareEvaluations, getEvaluation } from "./api";
import { evidenceMetricLabels } from "./benchmark-metrics";
import "./semantic-evidence.css";

const stateLabels = {
  exact_only: "Exact-only baseline · combined evaluation pending",
  pending: "Exact-only baseline · combined evaluation pending or interrupted",
  complete: "Combined evaluation complete",
  complete_with_failures: "Combined evaluation finished with failures",
};
const verdicts = ["Equivalent", "Partially Equivalent", "Not Equivalent", "Uncertain"] as const;
const statuses = {
  judged: "Judged",
  no_eligible_comparison: "No eligible comparison",
  invalid_judgment: "Invalid judgment",
  deterministic_delivery_failure: "Delivery failure",
  unattempted: "Unattempted",
  awaiting_receipt: "Awaiting receipt",
  interrupted: "Interrupted attempt",
  provider_failed: "Provider failure",
};
const readable = (value: string) => value.replaceAll("_", " ");
const number = new Intl.NumberFormat("en", { maximumFractionDigits: 3 });
const usd = new Intl.NumberFormat("en", { style: "currency", currency: "USD", maximumFractionDigits: 4 });

function Disclosure({ label, children }: { label: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <details className="semantic-evidence" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>{label}</summary>
      {open && <div className="semantic-evidence-content">{children}</div>}
    </details>
  );
}

export function PCGEvaluation({ run, children }: { run: RunDetail; children: ReactNode }) {
  return (
    <>
      <h3>PCG Evaluation</h3>
      {run.benchmark_v4?.state === "complete" ? <CompletedRunEvaluation run={run}>{children}</CompletedRunEvaluation> : (
        <>
          <p role="status">Evaluation is provisional until the Benchmark Run finishes.</p>
          <MetricCards metrics={evaluationMetrics(undefined, run)} />
          {children}
        </>
      )}
    </>
  );
}

function CompletedRunEvaluation({ run, children }: { run: RunDetail; children: ReactNode }) {
  const load = useCallback((signal: AbortSignal) => getEvaluation(run.id, signal), [run.id]);
  const { data, error, retry } = useRead(load);
  return (
    <>
      <p role="status" className="evaluation-state">
        {data ? stateLabels[data.state] : error ? "Evaluation unavailable" : "Loading evaluation"}
      </p>
      <MetricCards metrics={evaluationMetrics(data, run)} />
      {error && <ReadState error={error} retry={retry} />}
      {children}
      {data && <Disclosure label="Evidence diagnostics">
        <AssessmentDetails assessment={data} />
        <button className="secondary" onClick={retry}>Refresh evaluation</button>
      </Disclosure>}
    </>
  );
}

function evaluationMetrics(evaluation?: SemanticRunSummary, run?: RunDetail) {
  const graph = evaluation ? evaluation.graph_f1 : run?.quality ? run.quality.qualified_graph : run?.benchmark_v4?.qualified;
  const summary = evaluation?.target_summary;
  const support = summary?.evidence_support;
  const completion = summary?.proof_completion;
  const coverage = summary?.multi_source_evidence_coverage;
  const exactProof = run?.quality?.complete_proof;
  const exactCoverage = run?.quality?.joint_only_coverage;
  return [
    {
      label: "Graph F1", rate: graph?.f1 ?? null, basis: graph ? `${graph.inputs} qualified Conditions` : "",
      description: "Relationship correctness",
    },
    {
      label: "Evidence Support", rate: support?.rate ?? null,
      basis: support ? `${support.count}/${support.targets} formal targets` : "",
      description: "At least one required member matched",
    },
    {
      label: evidenceMetricLabels.complete_proof, rate: completion?.rate ?? exactProof?.rate ?? null,
      basis: completion ? `${completion.count}/${completion.targets} formal targets`
        : exactProof?.rate != null ? `${exactProof.complete}/${exactProof.targets} formal targets` : "",
      description: "All members of an approved alternative matched",
    },
    {
      label: evidenceMetricLabels.joint_only_coverage, rate: coverage?.mean ?? exactCoverage?.mean ?? null,
      basis: coverage ? `${number.format(coverage.matched_target_equivalents)}/${coverage.targets} target-equivalents`
        : exactCoverage ? `${exactCoverage.targets} Multi-Source targets` : "",
      description: "Mean best-alternative coverage",
    },
  ];
}

function MetricCards({ metrics }: { metrics: ReturnType<typeof evaluationMetrics> }) {
  return (
    <dl className="quality-card-grid" aria-label="Evaluation metrics">
      {metrics.map(({ label, rate, basis, description }) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{percentMetric(rate)}</dd>
          <dd className="quality-scope">{description}{basis && <small>{basis}</small>}</dd>
        </div>
      ))}
    </dl>
  );
}

function EvidenceCounts({ summary }: { summary: SemanticSummary }) {
  const judgedPairs = Object.values(summary.pair_verdicts).reduce((total, count) => total + count, 0);
  const gaps = assessmentGaps(summary.semantic_outcomes);
  const pairCoverage = summary.candidate_pairs
    ? `${judgedPairs}/${summary.candidate_pairs} eligible pairs judged`
    : "No eligible pairs to judge";
  return (
    <dl className="semantic-diagnostics">
      <div>
        <dt>Judgment Coverage</dt>
        <dd>{pairCoverage} · {summary.pair_verdicts["Partially Equivalent"] ?? 0} partially equivalent
          {gaps && ` · ${gaps}`}</dd>
      </div>
      <div>
        <dt>Required evidence members</dt>
        <dd>{summary.exact_matched_members} exact · {summary.additional_matched_members} equivalent added · {summary.unmatched_required_members} unmatched
          {" · "}{countLabel(summary.newly_completed_proofs, "newly completed proof")}</dd>
      </div>
    </dl>
  );
}

function AssessmentDetails({ assessment }: { assessment: SemanticEvidenceReport }) {
  const { target_summary: summary, evaluator } = assessment;
  return (
    <>
      <p className="semantic-note">{assessment.scope_note}</p>
      {assessment.state === "pending" && <p>Retained decisions are shown below. The headline scores still use exact matches.</p>}
      {assessment.state === "complete_with_failures" && <p>Invalid responses and provider failures earned no additional evidence credit.</p>}
      <EvidenceCounts summary={summary} />
      {assessment.operations && <ExecutionUsage operations={assessment.operations} />}
      <VerdictCounts verdictCounts={summary.pair_verdicts} />
      <Targets targets={assessment.targets} />
      <details>
        <summary>Evaluator and execution record</summary>
        <dl className="semantic-metadata">
          <dt>Methodology</dt><dd>{assessment.methodology}</dd>
          <dt>Matching contract</dt><dd>{evaluator.version}</dd>
          <dt>Judge</dt><dd>DeepSeek · {evaluator.model} · temperature {evaluator.settings.temperature} · {evaluator.settings.max_retries} retries</dd>
          <dt>Prompt SHA-256</dt><dd>{evaluator.prompt_sha256}</dd>
          <dt>Plan SHA-256</dt><dd>{assessment.plan_sha256 ?? "Evaluation plan not prepared"}</dd>
        </dl>
      </details>
    </>
  );
}

function VerdictCounts({ verdictCounts }: { verdictCounts: SemanticSummary["pair_verdicts"] }) {
  return <ul className="semantic-counts" aria-label="Semantic verdict distribution">
    {verdicts.map((verdict) => <li key={verdict}>{verdict} <strong>{verdictCounts[verdict] ?? 0}</strong></li>)}
  </ul>;
}

function countLabel(count: number, label: string) {
  return `${count} ${label}${count === 1 ? "" : "s"}`;
}

function assessmentGaps(outcomes: SemanticSummary["semantic_outcomes"]) {
  return Object.entries(outcomes)
    .filter(([state, count]) => state !== "judged" && state !== "no_eligible_comparison" && count > 0)
    .map(([state, count]) => {
      const label = statuses[state as keyof typeof statuses].toLowerCase();
      return `${count} ${count === 1 || state === "unattempted" || state === "awaiting_receipt" ? label : `${label}s`}`;
    }).join(" · ");
}

function ExecutionUsage({ operations }: { operations: SemanticOperations }) {
  return <p className="semantic-usage">{operations.reserved_attempts}/{operations.planned_attempts} attempts reserved · {operations.reused_judgments} reused ·{" "}
    {operations.known_estimated_peak_usd == null ? "No usage estimate" : `${usd.format(operations.known_estimated_peak_usd)} estimated at peak rates`}
    {operations.reserved_attempts_without_usage > 0 && ` · ${operations.reserved_attempts_without_usage} without usage`}
    {operations.mean_latency_seconds != null && ` · ${operations.mean_latency_seconds.toFixed(1)}s mean latency`}</p>;
}

function Targets({ targets }: { targets: SemanticTarget[] }) {
  const [filter, setFilter] = useState("all");
  const visible = targets.filter((item) => filter === "all" || item.status === filter ||
    item.decisions.some((decision) => decision.verdict === filter) || (filter === "added" && item.semantic_members.length > 0));
  return (
    <details>
      <summary>Inspect formal targets ({targets.length})</summary>
      <label className="semantic-filter">Filter formal targets
        <select value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="all">All outcomes</option>
          <option value="added">Added semantic matches</option>
          {verdicts.map((verdict) => <option key={verdict}>{verdict}</option>)}
          {Object.entries(statuses).filter(([state]) => state !== "judged").map(([state, label]) =>
            <option key={state} value={state}>{label}</option>)}
        </select>
      </label>
      <p role="status">{visible.length} of {targets.length} formal targets</p>
      {visible.map((row) => <Target key={row.id} row={row} />)}
    </details>
  );
}

function relationship(edge: SemanticTarget["edge"]) {
  return `${edge[0]} · ${readable(edge[1])} · ${edge[2]}`;
}

function Target({ row }: { row: SemanticTarget }) {
  const [open, setOpen] = useState(false);
  return (
    <details className="semantic-target" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>
        {row.condition} · {relationship(row.edge)}{" "}
        <strong>{row.routes.some((route) => route.complete) ? "Complete proof" : "Incomplete proof"}</strong>
      </summary>
      {open && <div className="semantic-target-content">
        <p>Exact outcome · {readable(row.deterministic.exact_outcome)} · {statuses[row.status]}</p>
        {row.reuse && <p>Reused from Run <code>{row.reuse.origin_run}</code></p>}
        {row.provider && <p className="semantic-usage">
          {row.provider.returned_model ?? "Provider response"} · {row.provider.latency_seconds.toFixed(1)}s
          {row.provider.status_code != null && ` · HTTP ${row.provider.status_code}`}
        </p>}
        {row.error && <p>{row.error}</p>}
        {row.invalid_response != null && <details>
          <summary>Retained invalid response</summary>
          <pre className="semantic-response">{row.invalid_response || "The response was empty."}</pre>
        </details>}
        <h4>Approved proof alternatives</h4>
        <ol>{row.routes.map((route, index) => (
          <li key={index}><strong>{route.complete ? "Complete" : "Incomplete"}</strong> · {route.matched_members.length}/{route.members.length} members matched · {route.members.join(", ")}</li>
        ))}</ol>
        <h4>Required evidence and matches</h4>
        {row.members.map((member) => <RequiredMember key={member.id} member={member} row={row} />)}
        <OtherQuotations row={row} />
      </div>}
    </details>
  );
}

function OtherQuotations({ row }: { row: SemanticTarget }) {
  if (row.quotations.length === 0) return <p>No quotations were attached.</p>;
  const shown = new Set([...Object.values(row.exact_matches), ...row.candidate_pairs.map((pair) => pair.quotation_id)]);
  const other = row.quotations.filter((quote) => !shown.has(quote.id));
  if (other.length === 0) return null;
  return <details>
    <summary>Other attached quotations ({other.length})</summary>
    {other.map((quote) => <Quotation key={quote.id} quote={quote} label="Actual PCG quotation" />)}
  </details>;
}

function RequiredMember({ member, row }: { member: SemanticQuotation; row: SemanticTarget }) {
  const exact = row.quotations.find((quote) => quote.id === row.exact_matches[member.id]);
  const pairs = row.candidate_pairs.filter((pair) => pair.member_id === member.id);
  const credited = !!exact || row.semantic_members.includes(member.id);
  return (
    <section className="semantic-member">
      <Quotation quote={member} label={credited ? "Required evidence" : "Required evidence · Unmatched"} />
      {exact ? <Quotation quote={exact} label="Exact match · actual PCG quotation" /> :
        pairs.length === 0 ? <p>No attached quotation from this Source.</p> :
          pairs.map((pair) => {
            const quote = row.quotations.find((item) => item.id === pair.quotation_id);
            const decision = row.decisions.find((item) => item.member_id === member.id && item.quotation_id === pair.quotation_id);
            return <div key={pair.quotation_id} className="semantic-pair">
              {quote && <Quotation quote={quote} label="Actual PCG quotation" />}
              <p><strong>{decision?.verdict ?? statuses[row.status]}</strong>{decision && ` · ${decision.reason}`}</p>
              {!!decision?.material_differences.length && <ul>{decision.material_differences.map((difference, index) =>
                <li key={index}>{difference}</li>)}</ul>}
            </div>;
          })}
    </section>
  );
}

function Quotation({ quote, label }: { quote: SemanticQuotation; label: string }) {
  return <blockquote>
    <p><strong>{label} · {quote.id}</strong> · Source <code>{quote.source_id}</code></p>
    <p>{quote.text}</p>
  </blockquote>;
}

export function PCGEvaluationComparison({ left, right }: { left: string; right: string }) {
  const [all, setAll] = useState(false);
  const load = useCallback((signal: AbortSignal) => compareEvaluations(left, right, signal), [left, right]);
  const { data, error, retry } = useRead(load);
  if (!data) return <ReadState error={error} retry={retry} />;
  const rows = all ? data.transitions : data.transitions.filter(changed);
  return (
    <>
      <EvaluationComparisonTable left={data.left} right={data.right} comparable={data.comparable} />
      {!data.comparable && <p>Changes are available after both combined evaluations complete without invalid responses or provider failures.</p>}
      <button className="secondary" onClick={retry}>Refresh comparison</button>
      <Disclosure label="Evidence comparison diagnostics">
        <div className="semantic-comparison">
          <div>
            <h4>Comparison Run</h4>
            <EvidenceCounts summary={data.left.target_summary} />
            {data.left.operations && <ExecutionUsage operations={data.left.operations} />}
          </div>
          <div>
            <h4>Selected Run</h4>
            <EvidenceCounts summary={data.right.target_summary} />
            {data.right.operations && <ExecutionUsage operations={data.right.operations} />}
          </div>
        </div>
        {data.comparable && <>
          <p>{data.paired_valid_targets}/{data.formal_targets} formal targets have valid judgments in both Runs.</p>
          <label className="semantic-filter"><input type="checkbox" checked={all} onChange={(event) => setAll(event.target.checked)} />
            Show every formal target
          </label>
          <p role="status">{rows.length} of {data.formal_targets} formal targets</p>
          {rows.map((row) => (
            <details className="semantic-target" key={row.id}>
              <summary>{row.condition} · {relationship(row.edge)}</summary>
              <p>{outcome(row.left)} → {outcome(row.right)}</p>
              {row.changed_members.length > 0 && <ul>{row.changed_members.map((member) => (
                <li key={member.member_id}><strong>{member.member_id} · {member.left} → {member.right}</strong> · Source <code>{member.source_id}</code><br />
                  {member.quotation}</li>
              ))}</ul>}
            </details>
          ))}
        </>}
      </Disclosure>
    </>
  );
}

function EvaluationComparisonTable({ left, right, comparable }: {
  left: SemanticRunSummary; right: SemanticRunSummary; comparable: boolean;
}) {
  const comparisonMetrics = evaluationMetrics(left);
  return (
    <div className="table-scroll semantic-metric-comparison">
      <table>
        <caption>PCG Evaluation comparison</caption>
        <thead><tr>
          <th scope="col">Metric</th>
          <th scope="col">Comparison Run<small>{stateLabels[left.state]}</small></th>
          <th scope="col">Selected Run<small>{stateLabels[right.state]}</small></th>
          {comparable && <th scope="col">Change</th>}
        </tr></thead>
        <tbody>{evaluationMetrics(right).map((metric, index) => {
          const before = comparisonMetrics[index];
          return (
            <tr key={metric.label}>
              <th scope="row">{metric.label}</th>
              {[before, metric].map(({ rate, basis }, side) => (
                <td key={side}><strong>{percentMetric(rate)}</strong><small>{basis}</small></td>
              ))}
              {comparable && <td>{percentagePointChange(before.rate, metric.rate)}</td>}
            </tr>
          );
        })}</tbody>
      </table>
    </div>
  );
}

function percentagePointChange(before: number | null, after: number | null) {
  if (before === null || after === null) return "Unavailable";
  const change = 100 * (after - before);
  return `${change > 0 ? "+" : ""}${change.toFixed(2)} pp`;
}

function outcome(value: SemanticOutcome) {
  return `${value.complete ? "Complete proof" : "Incomplete proof"} · ${statuses[value.status]}${value.reused ? " (reused)" : ""}`;
}

function changed(row: SemanticTransition) {
  return row.left.status !== row.right.status || row.left.complete !== row.right.complete ||
    row.left.exact_outcome !== row.right.exact_outcome || row.changed_members.length > 0;
}
