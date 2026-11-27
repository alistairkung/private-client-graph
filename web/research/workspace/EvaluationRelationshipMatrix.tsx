import type { DeliveredGraphMetrics, EvidenceAdjustedF1, SemanticEvidenceReport } from "../shared/contracts";
import { RunRelationshipMatrix } from "./RunRelationshipMatrix";

export function EvaluationRelationshipMatrix({ graph, evaluation, expectedEdgesWithoutGraph }: {
  graph: DeliveredGraphMetrics;
  evaluation?: SemanticEvidenceReport;
  expectedEdgesWithoutGraph: number;
}) {
  const adjusted = evaluation?.evidence_adjusted_f1;
  const population = evaluation?.proof_population;
  const proof = evaluation?.target_summary.proof_completion;
  const breakdown = adjusted && population && proof ? {
    complete: proof.count,
    incomplete: adjusted.incomplete_recovered_proofs,
    withoutFormalTarget: population.true_positives_without_formal_targets,
  } : undefined;

  return (
    <>
      <RunRelationshipMatrix
        counts={graph.counts}
        expectedEdgesWithoutGraph={expectedEdgesWithoutGraph}
        scope={`${graph.inputs} qualified Conditions`}
        caption={breakdown ? "Evidence-aware confusion matrix" : undefined}
        proofBreakdown={breakdown}
      />
      {adjusted && population && proof && <EvidencePenalty
        adjusted={adjusted}
        unrecovered={population.unrecovered_formal_targets}
        formalTargets={proof.targets}
      />}
    </>
  );
}

function EvidencePenalty({ adjusted, unrecovered, formalTargets }: {
  adjusted: EvidenceAdjustedF1;
  unrecovered: number;
  formalTargets: number;
}) {
  const weight = (adjusted.weight_numerator / adjusted.weight_denominator).toFixed(4);
  const equivalenceCompletions = adjusted.proofs_completed_by_equivalence;
  return (
    <section className="run-matrix-penalty" aria-label="Evidence-Adjusted F1 calculation">
      <div className="run-matrix-penalty-strip">
        <div>
          <h5>Evidence penalty</h5>
          <p>{adjusted.incomplete_recovered_proofs} incomplete proofs × {weight}</p>
        </div>
        <strong>{adjusted.penalty_units.toFixed(2)} units</strong>
      </div>
      <details className="run-matrix-formula">
        <summary>Formula and counting rules</summary>
        <p><code>2TP / (2TP + FP + FN + αU)</code></p>
        <p>α = {adjusted.weight_numerator}/{adjusted.weight_denominator} ≈ {weight}</p>
        <p>U counts true positives with incomplete formal proofs. They add weight to the denominator and remain true positives.</p>
        <p>{unrecovered} of {formalTargets} formal targets were unrecovered and count as false negatives.
          {" "}True positives without a formal proof target carry no evidence penalty.</p>
        {equivalenceCompletions > 0 && <p>{equivalenceCompletions} {equivalenceCompletions === 1 ? "proof" : "proofs"} completed through equivalence.</p>}
      </details>
    </section>
  );
}
