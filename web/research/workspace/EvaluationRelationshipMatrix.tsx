import { percentMetric } from "../../src/shared/research/presentation";
import type { DeliveredGraphMetrics, EvidenceAdjustedF1, SemanticEvidenceReport } from "../shared/contracts";
import { RunRelationshipMatrix } from "./RunRelationshipMatrix";

export function EvaluationRelationshipMatrix({ graph, evaluation, expectedEdgesWithoutGraph }: {
  graph: DeliveredGraphMetrics | null | undefined;
  evaluation?: SemanticEvidenceReport;
  expectedEdgesWithoutGraph: number;
}) {
  if (!graph) return null;
  const adjusted = evaluation?.evidence_adjusted_f1;
  const population = evaluation?.proof_population;
  const proof = evaluation?.target_summary.proof_completion;
  const breakdown = adjusted && population && proof ? {
    complete: proof.count,
    incomplete: adjusted.incomplete_recovered_proofs,
    withoutFormalTarget: population.true_positives_without_formal_targets,
  } : undefined;

  return (
    <div className={breakdown ? "protocol-results-matrix evidence-aware-matrix" : "protocol-results-matrix"}>
      <RunRelationshipMatrix
        counts={graph.counts}
        expectedEdgesWithoutGraph={expectedEdgesWithoutGraph}
        scope={`${graph.inputs} qualified Conditions`}
        proofBreakdown={breakdown}
      />
      {adjusted && population && proof && <EvidencePenalty
        adjusted={adjusted}
        graphF1={graph.f1}
        unrecovered={population.unrecovered_formal_targets}
        formalTargets={proof.targets}
      />}
    </div>
  );
}

function EvidencePenalty({ adjusted, graphF1, unrecovered, formalTargets }: {
  adjusted: EvidenceAdjustedF1;
  graphF1: number;
  unrecovered: number;
  formalTargets: number;
}) {
  const weight = (adjusted.weight_numerator / adjusted.weight_denominator).toFixed(4);
  const equivalenceCompletions = adjusted.proofs_completed_by_equivalence;
  return (
    <section className="run-matrix-penalty" aria-label="Evidence-Adjusted F1 calculation">
      <h4>Evidence-Adjusted F1 calculation</h4>
      <p><code>2TP / (2TP + FP + FN + αU)</code></p>
      <p>
        <span>U = {adjusted.incomplete_recovered_proofs}</span>{" · "}
        <span>α = {adjusted.weight_numerator}/{adjusted.weight_denominator} ≈ {weight}</span>
      </p>
      <dl>
        <div>
          <dt>Evidence penalty</dt>
          <dd>{adjusted.incomplete_recovered_proofs} × {weight} ≈ <strong>{adjusted.penalty_units.toFixed(2)}</strong> penalty units</dd>
        </div>
        <div><dt>Graph F1</dt><dd>{percentMetric(graphF1)}</dd></div>
        <div><dt>Evidence-Adjusted F1</dt><dd><strong>{percentMetric(adjusted.f1)}</strong></dd></div>
      </dl>
      <p>U counts true positives with incomplete formal proofs. They remain true positives and add weight to the denominator.</p>
      <p>{unrecovered} of {formalTargets} formal targets were unrecovered and count as false negatives.
        True positives without a formal proof target carry no evidence penalty.</p>
      {equivalenceCompletions > 0 && <p>{equivalenceCompletions} {equivalenceCompletions === 1 ? "proof" : "proofs"} completed through equivalence.</p>}
    </section>
  );
}
