import { useCallback, useState, type ReactNode } from "react";
import type {
  SemanticOutcome, SemanticRunSummary, SemanticTarget, SemanticTransition,
} from "../shared/contracts";
import { ReadState } from "../shared/presentation";
import { useRead } from "../shared/useRead";
import { compareSemanticEvidence, getSemanticEvidence } from "./api";
import { evidenceMetricLabels } from "./benchmark-metrics";
import "./semantic-evidence.css";

const title = "Semantic Evidence — AI-assessed, unverified";
const timingWithoutCutoff = "timing (assessment cutoff unavailable)";
const verdicts = ["Supported", "Partially Supported", "Unsupported", "Uncertain"] as const;
const statuses = {
  judged: "Judged",
  invalid_judgment: "Invalid judgment",
  deterministic_delivery_failure: "Delivery failure",
  unattempted: "Unattempted",
  awaiting_receipt: "Awaiting receipt",
  interrupted: "Interrupted attempt",
  provider_failed: "Provider failure",
};
const flags: Record<string, string> = {
  potentially_sufficient_overlooked_by_exact_matching: "Potentially sufficient evidence missed by exact matching",
  potential_new_partial_support: "Potential partial support from a non-matching quotation",
  exact_complete_not_called_supported: "Exact proof complete · AI did not return Supported",
  joint_only_supported_with_one_cited_source: "Multi-Source target · Supported using one cited Source",
  supported_control: "Control returned Supported",
};
const readable = (value: string) => value.replaceAll("_", " ");
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

export function SemanticEvidencePanel({ run }: { run: string }) {
  return <Disclosure label={title}><RunAssessment key={run} run={run} /></Disclosure>;
}

function RunAssessment({ run }: { run: string }) {
  const load = useCallback((signal: AbortSignal) => getSemanticEvidence(run, signal), [run]);
  const { data, error, retry } = useRead(load);
  if (data === undefined) return <ReadState error={error} retry={retry} />;
  if (!data) return (
    <>
      <p>No semantic assessment is recorded for this Run. The Workbench operator can prepare one from the retained Run.</p>
      <button className="secondary" onClick={retry}>Refresh assessment</button>
    </>
  );
  return (
    <>
      <p className="semantic-note"><strong>Temporal limitation.</strong> {data.temporal_limitation}</p>
      <Coverage summary={data} />
      <p className="semantic-note">DeepSeek assesses attached quotations. The judge and extractor can share model-specific biases.</p>
      <Targets targets={data.targets} />
      <details>
        <summary>Sanity controls ({data.controls.length})</summary>
        {data.controls.map((row) => <Target key={row.id} row={row} />)}
      </details>
      <details>
        <summary>Evaluator and execution record</summary>
        <dl className="semantic-metadata">
          <dt>Evaluator</dt><dd>{data.evaluator.version}</dd>
          <dt>Judge</dt><dd>{data.evaluator.model} · temperature {data.evaluator.settings.temperature} · {data.evaluator.settings.max_retries} retries</dd>
          <dt>Prompt SHA-256</dt><dd>{data.evaluator.prompt_sha256}</dd>
          <dt>Plan SHA-256</dt><dd>{data.plan_sha256}</dd>
        </dl>
      </details>
      <button className="secondary" onClick={retry}>Refresh assessment</button>
    </>
  );
}

function Coverage({ summary }: { summary: SemanticRunSummary }) {
  const { target_summary: coverage, operations } = summary;
  const potential = coverage.potentially_sufficient_overlooked_by_exact_matching;
  return (
    <div className="semantic-coverage">
      <p><strong>{coverage.semantic_outcomes.judged ?? 0}/{coverage.formal_targets} valid judgments</strong> ·{" "}
        {coverage.recovered_targets} recovered targets</p>
      <ul className="semantic-counts" aria-label="Semantic verdict distribution">
        {verdicts.map((verdict) => <li key={verdict}>{verdict} <strong>{coverage.verdicts[verdict] ?? 0}</strong></li>)}
      </ul>
      <p>{Object.entries(coverage.semantic_outcomes).filter(([state, count]) => state !== "judged" && count > 0)
        .map(([state, count]) => `${count} ${statuses[state as keyof typeof statuses].toLowerCase()}`).join(" · ")}</p>
      <p>{potential.count ?? "Unavailable"} potentially sufficient missed proofs ·{" "}
        {potential.recovered_exact_incomplete_judged}/{potential.recovered_exact_incomplete_denominator} recovered exact-incomplete targets judged</p>
      <p>{operations.reserved_attempts}/{operations.planned_attempts} attempts reserved · {operations.reused_judgments} reused ·{" "}
        {operations.known_estimated_peak_usd == null ? "No usage estimate" : `${usd.format(operations.known_estimated_peak_usd)} estimated at peak rates`}
        {operations.reserved_attempts_without_usage > 0 && ` · ${operations.reserved_attempts_without_usage} without usage`}
        {operations.mean_latency_seconds != null && ` · ${operations.mean_latency_seconds.toFixed(1)}s mean latency`}</p>
    </div>
  );
}

function Targets({ targets }: { targets: SemanticTarget[] }) {
  const [filter, setFilter] = useState("all");
  const visible = targets.filter((item) => filter === "all" || item.status === filter ||
    item.judgment?.verdict === filter || (filter === "disagreements" && item.flags.length > 0));
  return (
    <details>
      <summary>Inspect formal targets ({targets.length})</summary>
      <label className="semantic-filter">Filter formal targets
        <select value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="all">All outcomes</option>
          <option value="disagreements">Evidence disagreements</option>
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
  const baseline = row.deterministic;
  return (
    <details className="semantic-target" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>
        {row.condition ?? readable(row.control ?? "Control")} · {relationship(row.edge)}{" "}
        <strong>{row.judgment?.verdict ?? statuses[row.status]}</strong>
      </summary>
      {open && <div className="semantic-target-content">
        {baseline && <p>Exact outcome · {readable(baseline.exact_outcome)}
          {baseline.joint_only && ` · ${evidenceMetricLabels.joint_only_coverage} ${(baseline.best_exact_pair_coverage * 100).toFixed(1)}%`}
        </p>}
        {row.flags.map((flag) => <p key={flag}>{flags[flag] ?? readable(flag)}</p>)}
        {row.reuse && <p>Reused from Run <code>{row.reuse.origin_run}</code></p>}
        {row.error && <p>{row.error}</p>}
        {row.invalid_response != null && <details>
          <summary>Retained invalid response</summary>
          <pre className="semantic-response">{row.invalid_response || "The response was empty."}</pre>
        </details>}
        {row.judgment && <>
          <h4>Documentary facts</h4>
          <ul>{row.judgment.facts.map((fact) => (
            <li key={fact.fact}>
              <strong>{fact.fact === "timing" && row.control === null ? timingWithoutCutoff : readable(fact.fact)} · {fact.status}</strong>{" "}
              {fact.quotation_ids.length > 0 && <span>({fact.quotation_ids.join(", ")}) </span>}{fact.reason}</li>
          ))}</ul>
        </>}
        {row.quotations.length > 0 && <>
          <h4>Attached quotations</h4>
          {row.quotations.map((quote) => <blockquote key={quote.id}>
            <p><strong>{quote.id}</strong> · Source <code>{quote.source_id}</code></p>
            <p>{quote.text}</p>
          </blockquote>)}
        </>}
      </div>}
    </details>
  );
}

export function SemanticEvidenceComparison({ left, right }: { left: string; right: string }) {
  return <Disclosure label={`${title} comparison`}><Comparison key={`${left}/${right}`} left={left} right={right} /></Disclosure>;
}

function Comparison({ left, right }: { left: string; right: string }) {
  const [all, setAll] = useState(false);
  const load = useCallback((signal: AbortSignal) => compareSemanticEvidence(left, right, signal), [left, right]);
  const { data, error, retry } = useRead(load);
  if (data === undefined) return <ReadState error={error} retry={retry} />;
  if (!data) return <p>Both Runs need a recorded semantic assessment to compare their formal targets.</p>;
  const rows = all ? data.transitions : data.transitions.filter(changed);
  return (
    <>
      <p className="semantic-note"><strong>Temporal limitation.</strong> {data.temporal_limitation}</p>
      <p><strong>{data.paired_valid_targets}/{data.formal_targets} formal targets have two valid judgments.</strong>{" "}
        Fact transitions are shown only for those pairs.</p>
      <div className="semantic-comparison">
        <div><h4>Comparison Run</h4><Coverage summary={data.left} /></div>
        <div><h4>Selected Run</h4><Coverage summary={data.right} /></div>
      </div>
      <label className="semantic-filter"><input type="checkbox" checked={all} onChange={(event) => setAll(event.target.checked)} />
        Show every formal target
      </label>
      <p role="status">{rows.length} of {data.formal_targets} formal targets</p>
      {rows.map((row) => (
        <details className="semantic-target" key={row.id}>
          <summary>{row.condition} · {relationship(row.edge)}</summary>
          <p>{outcome(row.left)} → {outcome(row.right)}</p>
          <p>Exact outcome · {readable(row.left.exact_outcome)} → {readable(row.right.exact_outcome)}</p>
          {!row.facts_comparable && <p>Two valid judgments are required to compare documentary facts.</p>}
          {row.changed_facts.length > 0 && <ul>{row.changed_facts.map((fact) =>
            <li key={fact.fact}>{fact.fact === "timing" ? timingWithoutCutoff : fact.fact} · {fact.left} → {fact.right}</li>)}</ul>}
        </details>
      ))}
    </>
  );
}

function outcome(value: SemanticOutcome) {
  const verdict = value.verdict ?? statuses[value.status];
  return value.reused ? `${verdict} (reused)` : verdict;
}

function changed(row: SemanticTransition) {
  return row.left.status !== row.right.status || row.left.verdict !== row.right.verdict ||
    row.left.exact_outcome !== row.right.exact_outcome || row.changed_facts.length > 0;
}
