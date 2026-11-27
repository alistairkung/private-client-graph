import type { GraphCounts } from "../shared/contracts";

export function RunRelationshipMatrix({
  counts,
  expectedEdgesWithoutGraph,
  scope = "All conditions",
}: {
  counts: GraphCounts;
  expectedEdgesWithoutGraph: number;
  scope?: string;
}) {
  return (
    <figure className="run-matrix">
      <table className="run-matrix-table">
        <caption>Relationship confusion matrix · {scope}</caption>
        <thead>
          <tr>
            <th scope="col">Expected</th>
            <th scope="col">Predicted present</th>
            <th scope="col">Predicted absent</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Present</th>
            <td className="run-matrix-correct">
              <strong>{counts.tp}</strong> <span>TP · Correct</span>
            </td>
            <td className="run-matrix-missing">
              <strong>{counts.fn}</strong> <span>FN · Missing</span>
            </td>
          </tr>
          <tr>
            <th scope="row">Absent</th>
            <td className="run-matrix-unsupported">
              <strong>{counts.fp}</strong> <span>FP · Unsupported</span>
            </td>
            <td className="run-matrix-unscored">
              <span aria-hidden="true">—</span> <span>TN · Unscored</span>
            </td>
          </tr>
        </tbody>
      </table>
      {expectedEdgesWithoutGraph > 0 && (
        <figcaption>
          FN includes {expectedEdgesWithoutGraph} expected relationships from conditions without a valid graph.
        </figcaption>
      )}
    </figure>
  );
}
