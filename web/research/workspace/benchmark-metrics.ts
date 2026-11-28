export const evidenceMetricLabels = {
  combined_graph: "Combined Graph F1",
  qualified_graph: "Qualified Graph F1",
  evidence_adjusted: "Evidence-Adjusted F1",
  evidence_support: "Evidence Support",
  complete_proof: "Proof Completion",
  joint_only_coverage: "Multi-Source Evidence Coverage",
} as const;

export const multiSourceProofCompletionLabel = "Multi-Source Proof Completion";
export function formatF1Basis(tp: number, fp: number, fn: number) {
  const numerator = 2 * tp;
  const denominator = numerator + fp + fn;
  return denominator === 0
    ? "0/0 · zero-edge case"
    : `${numerator}/${denominator} basis`;
}
