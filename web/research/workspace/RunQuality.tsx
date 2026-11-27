import type { BenchmarkV4Comparison, QualityProjection, RelationshipScore } from "../shared/contracts";

export const percent = (value: number | null | undefined) =>
  value == null ? "Unavailable" : `${(100 * value).toFixed(2)}%`;

export function RunQuality({ quality, mixed = false, provisional = false }: {
  quality: QualityProjection; mixed?: boolean; provisional?: boolean;
}) {
  const graphScope = mixed ? `${quality.planned_inputs} inputs · mixed references` : `${quality.qualified_inputs} qualified Conditions`;
  const qualifiedScope = `${quality.qualified_inputs} qualified Conditions`;
  const incomplete = provisional || quality.observed_inputs < quality.planned_inputs;
  return (
    <>
      <div className="run-quality-headlines">
        <QualityMeasure label="Graph F1" value={quality.graph} scope={graphScope}
          description="Did PCG identify the correct relationships?" />
        <QualityMeasure label="Evidence-Grounded F1" value={quality.grounded} scope={qualifiedScope}
          description="Did PCG identify the correct relationships and substantiate them sufficiently?" />
      </div>
      {incomplete && <p role="status">{quality.observed_inputs ? "Provisional" : "Awaiting observations"} · {quality.observed_inputs}/{quality.planned_inputs} inputs observed · {quality.observed_qualified_inputs}/{quality.qualified_inputs} qualified Conditions observed.</p>}
      {mixed && <p>Graph F1 on the qualified cohort <strong>{percent(quality.qualified_graph?.f1)}</strong></p>}
      {incomplete && <dl className="run-quality-outcomes">
        <div><dt>Processing</dt><dd>{quality.outcomes.processing ?? 0}</dd></div>
        <div><dt>Not yet executed</dt><dd>{quality.outcomes.not_attempted ?? 0}</dd></div>
      </dl>}
    </>
  );
}

function QualityMeasure({ label, value, scope, description }: {
  label: string; value: RelationshipScore | null; scope: string; description: string;
}) {
  return (
    <div className="run-quality-measure">
      <span>{label}</span>
      <strong>{percent(value?.f1)}</strong>
      <small>{scope}</small>
      <small>{description}</small>
      {value && <small>{value.counts.tp} true positives · {value.counts.fp} false positives · {value.counts.fn} false negatives</small>}
    </div>
  );
}

export function QualityDiagnostics({ quality }: { quality: QualityProjection }) {
  const { grounded, complete_proof: proof, joint_only_proof: joint, outcomes } = quality;
  return (
    <>
      {grounded && <p>Grounded precision {percent(grounded.precision)} · recall {percent(grounded.recall)} · {grounded.counts.tp} TP / {grounded.counts.fp} FP / {grounded.counts.fn} FN</p>}
      <p>Grounded F1 requires a complete formal proof. Some expected relationships have no formal proof target.</p>
      <p>Complete Proof Rate {percent(proof.rate)} ({proof.complete}/{proof.targets}) · Joint-only Proof Rate {percent(joint.rate)} ({joint.complete}/{joint.targets})</p>
      <p>{outcomes.scored ?? 0} constructed graphs · {outcomes.validation_failure ?? 0} construction failures · {outcomes.provider_failure ?? 0} provider failures · {outcomes.parse_failure ?? 0} parsing failures · {outcomes.uncertain ?? 0} uncertain attempts</p>
    </>
  );
}

export function QualityComparison({ comparison }: { comparison: BenchmarkV4Comparison }) {
  const { left_quality: left, right_quality: right, quality_delta: delta } = comparison;
  if (!left || !right) return null;
  const rows = [
    { label: "Graph F1", scope: "Mixed references", key: "graph", qualified: false },
    { label: "Evidence-Grounded F1", scope: "Qualified cohort", key: "grounded", qualified: true },
    { label: "Graph F1", scope: "Qualified cohort", key: "qualified_graph", qualified: true },
  ] as const;
  return (
    <table className="run-quality-comparison">
      <caption>Run quality · observed / planned</caption>
      <thead><tr>
        <th scope="col">Metric</th><th scope="col">Other Run</th>
        <th scope="col">Selected Run</th><th scope="col">Change</th>
      </tr></thead>
      <tbody>{rows.map(({ label, scope, key, qualified }) => {
        const change = delta?.[key];
        return (
          <tr key={key}>
            <th scope="row">{label}<small>{scope}</small></th>
            <td><strong>{percent(left[key]?.f1)}</strong><small>{coverage(left, qualified)}</small></td>
            <td><strong>{percent(right[key]?.f1)}</strong><small>{coverage(right, qualified)}</small></td>
            <td>{change == null ? "—" : `${change > 0 ? "+" : ""}${(100 * change).toFixed(2)} pp`}</td>
          </tr>
        );
      })}</tbody>
    </table>
  );
}


function coverage(quality: QualityProjection, qualified: boolean) {
  return qualified
    ? `${quality.observed_qualified_inputs}/${quality.qualified_inputs} Conditions`
    : `${quality.observed_inputs}/${quality.planned_inputs} inputs`;
}
