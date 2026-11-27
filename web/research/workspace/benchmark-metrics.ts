export const evidenceMetricLabels = {
  combined_graph: "Combined Graph F1",
  qualified_graph: "Qualified Graph F1",
  complete_proof: "Proof Completion",
  joint_only_coverage: "Multi-Source Evidence Coverage",
} as const;

export const multiSourceProofCompletionLabel = "Multi-Source Proof Completion";
export const multiSourceEvidenceCoverageDescription =
  "Average percentage of required evidence recovered for relationships that need multiple Sources. Uses the best-matching approved proof route.";

export function formatF1Basis(tp: number, fp: number, fn: number) {
  const numerator = 2 * tp;
  const denominator = numerator + fp + fn;
  return denominator === 0
    ? "0/0 · zero-edge case"
    : `${numerator}/${denominator} basis`;
}
