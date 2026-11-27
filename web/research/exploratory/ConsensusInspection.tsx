import type { ConsensusReference, ConsensusRelationship } from "./api";

export function ConsensusInspection({
  reference,
  chooseSource,
}: {
  reference: ConsensusReference;
  chooseSource: (id: string) => void;
}) {
  const paths = reference.relationships.filter(
    (relation) => relation.counts.support >= reference.majority,
  );
  const disputed = reference.relationships.filter(
    (relation) => relation.counts.support < reference.majority,
  );
  return (
    <section className="consensus-reference" aria-labelledby="consensus-reference-title">
      <h2 id="consensus-reference-title">Ten-reviewer AI consensus — not Benchmark v3 qualified</h2>
      <p>Documentary cut-off {reference.cutoff}</p>
      <p>
        {paths.length} majority relationships ·{" "}
        {paths.filter((row) => row.counts.support === reference.reviewer_count).length} unanimous ·{" "}
        {paths.filter((row) => row.evidence_decision === "supported").length} evidence-adjudicated
      </p>
      <h3>Majority relationships</h3>
      {paths.length === 0 && <p>No relationship reached six affirmative votes.</p>}
      {paths.map((row) => <Proposition key={identity(row)} row={row} chooseSource={chooseSource} />)}
      {disputed.length > 0 && (
        <>
          <h3>Below the majority threshold</h3>
          {disputed.map((row) => <Proposition key={identity(row)} row={row} chooseSource={chooseSource} />)}
        </>
      )}
      {reference.reviewer_open_questions.length > 0 && (
        <details>
          <summary>Open questions raised by reviewers</summary>
          <ul>{reference.reviewer_open_questions.map((text, index) => <li key={index}>{text}</li>)}</ul>
        </details>
      )}
      <details>
        <summary>Scientific limitations</summary>
        <ul>{reference.limitations.map((text, index) => <li key={index}>{text}</li>)}</ul>
      </details>
    </section>
  );
}

function identity(row: ConsensusRelationship) {
  return JSON.stringify([row.source, row.predicate, row.target]);
}

function Proposition({
  row,
  chooseSource,
}: {
  row: ConsensusRelationship;
  chooseSource: (id: string) => void;
}) {
  const label = row.evidence_decision === "supported"
    ? "Evidence-adjudicated"
    : row.evidence_decision === "unresolved" ? "Evidence unresolved" : "Below majority";
  return (
    <details className="consensus-proposition">
      <summary>
        <strong>{row.source} · {row.predicate.replaceAll("_", " ")} · {row.target}</strong>
        <small>{row.counts.support}/10 support · {label}</small>
      </summary>
      <p>
        {row.counts.support} support · {row.counts.reject} reject ·{" "}
        {row.counts.uncertain} uncertain · {row.counts.omitted} omitted
      </p>
      {row.evidence_reason && <p>{row.evidence_reason}</p>}
      {row.routes.map((route, index) => (
        <details key={index}>
          <summary>{route.approved ? "Accepted documentary route" : "Submitted documentary route"} {index + 1}</summary>
          {route.members.map((member) => (
            <div key={JSON.stringify(member)}>
              <button type="button" className="secondary" onClick={() => chooseSource(member.source_id)}>
                Read Source {member.source_id}
              </button>
              <blockquote>{member.quote}</blockquote>
            </div>
          ))}
        </details>
      ))}
    </details>
  );
}
