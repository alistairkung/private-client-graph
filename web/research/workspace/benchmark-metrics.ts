export function formatF1Basis(tp: number, fp: number, fn: number) {
  const numerator = 2 * tp;
  const denominator = numerator + fp + fn;
  return denominator === 0
    ? "0/0 · zero-edge case"
    : `${numerator}/${denominator} basis`;
}
