import type {
  CanonicalState,
  ProofMember,
  ProofTarget,
  Source,
} from "../shared/contracts";
import { sourceSegments } from "../results/EvidenceInspector";

const symmetric = new Set(["spouse_of", "sibling_of"]);

export function edgeKey(source: string, type: string, target: string) {
  const endpoints = symmetric.has(type)
    ? [source, target].sort()
    : [source, target];
  return JSON.stringify([endpoints[0], type, endpoints[1]]);
}

export function graphEdgeKeys(state: CanonicalState) {
  const names = new Map(state.entities.map((item) => [item.id, item.name]));
  return state.relationships.map((edge) =>
    edgeKey(
      names.get(edge.source) ?? edge.source,
      edge.type,
      names.get(edge.target) ?? edge.target,
    ),
  );
}

export function BenchmarkProofs({
  targets,
  predicted,
  sources,
}: {
  targets: ProofTarget[];
  predicted: CanonicalState | null | undefined;
  sources: Source[];
}) {
  if (!targets.length)
    return <p>No sufficient evidence targets were annotated.</p>;
  const edges = predicted ? graphEdgeKeys(predicted) : [];
  const evidence = new Map(predicted?.evidence.map((item) => [item.id, item]));
  return (
    <section aria-label="Sufficient Evidence Alternatives">
      <h4>Sufficient Evidence Alternatives</h4>
      <ul aria-label="Proof outcomes">
        {targets.map((target) => {
          const key = edgeKey(...target.edge);
          const citedSources = new Set(
            predicted?.relationships[edges.indexOf(key)]?.evidence_ids.map(
              (id) => evidence.get(id)?.source_id,
            ),
          );
          return (
            <li key={key}>
              <strong>{target.edge.join(" · ")}</strong>
              <p>
                {target.joint_only ? "Joint-only · " : ""}
                {target.status.replaceAll("_", " ")}
              </p>
              {target.alternatives.map((alternative, index) => (
                <div key={index}>
                  <strong>Alternative {index + 1}</strong>
                  <ul>
                    {alternative.members.map((member) => (
                      <Member
                        key={JSON.stringify([member.source_id, member.text])}
                        member={member}
                        source={sources.find(
                          (source) => source.id === member.source_id,
                        )}
                        status={
                          member.attached
                            ? "Attached to this relationship"
                            : !predicted
                              ? "No predicted canonical graph"
                              : citedSources.has(member.source_id)
                                ? "Wrong quotation on this relationship"
                                : "Source missing from this relationship"
                        }
                      />
                    ))}
                  </ul>
                </div>
              ))}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function Member({
  member,
  source,
  status,
}: {
  member: ProofMember;
  source?: Source;
  status: string;
}) {
  return (
    <li>
      <code>{member.source_id}</code> · <q>{member.text}</q> · {status}
      {source && member.occurrences.length > 0 && (
        <details>
          <summary>View proof member in Source</summary>
          <article aria-label="Frozen proof Source">
            <h5>{source.title}</h5>
            <pre>
              {sourceSegments(source.text, {
                ...member,
                id: member.source_id,
              }).map(({ text, highlighted }, index) =>
                highlighted ? <mark key={index}>{text}</mark> : text,
              )}
            </pre>
          </article>
        </details>
      )}
    </li>
  );
}
