import type { GraphCounts } from "../shared/contracts";

type ProofBreakdown = {
  complete: number;
  incomplete: number;
  withoutFormalTarget: number;
};

export function RunRelationshipMatrix({
  counts,
  expectedEdgesWithoutGraph,
  scope = "All conditions",
  proofBreakdown,
}: {
  counts: GraphCounts;
  expectedEdgesWithoutGraph: number;
  scope?: string;
  proofBreakdown?: ProofBreakdown;
}) {
  return (
    <figure className="run-matrix">
      <table className={proofBreakdown ? "run-matrix-table run-matrix-table-evidence" : "run-matrix-table"}>
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
              {proofBreakdown && <TruePositiveProofs breakdown={proofBreakdown} />}
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

function TruePositiveProofs({ breakdown }: { breakdown: ProofBreakdown }) {
  return (
    <dl className="run-matrix-proof-breakdown">
      <div className="run-matrix-proof-complete">
        <dt>Complete approved proof</dt><dd>{breakdown.complete}</dd>
      </div>
      <div className="run-matrix-proof-incomplete">
        <dt>Incomplete formal proof</dt><dd>{breakdown.incomplete}</dd>
      </div>
      <div className="run-matrix-proof-unannotated">
        <dt>No formal proof target</dt><dd>{breakdown.withoutFormalTarget}</dd>
      </div>
    </dl>
  );
}
