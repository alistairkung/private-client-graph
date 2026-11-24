import type { FamilyResearchContext } from "../shared/contracts";

export function FamilyResearchPanel({
  context,
  axisDefinitions,
}: {
  context: FamilyResearchContext | undefined;
  axisDefinitions: Record<string, string>;
}) {
  if (!context) {
    return (
      <section className="family-research-context">
        <p className="family-context-unavailable">
          Research context unavailable for this Run.
        </p>
      </section>
    );
  }

  return (
    <section className="family-research-context">
      <div className="family-hypothesis">
        <h4>Adversarial Hypothesis</h4>
        <p>{context.shortcuts}</p>
        <details className="family-research-detail">
          <summary>
            Research detail ·{" "}
            {context.hypothesis_basis === "historical_admission"
              ? "Historical admission · intended difficulty"
              : "Versioned hypothesis"}
          </summary>
          <p>{context.hypothesis_text}</p>
          <p>{context.scope_limits}</p>
          <dl className="family-record-details">
            <div>
              <dt>Family revision</dt>
              <dd>{context.revision}</dd>
            </div>
            <div>
              <dt>Admitted dossier SHA-256</dt>
              <dd>{context.dossier_sha256}</dd>
            </div>
            {context.hypothesis && (
              <div>
                <dt>Bound hypothesis</dt>
                <dd>
                  {context.hypothesis.hypothesis_id} · revision{" "}
                  {context.hypothesis.revision} · SHA-256{" "}
                  {context.hypothesis.hypothesis_sha256}
                </dd>
              </div>
            )}
          </dl>
          <h5>Difficulty axis definitions</h5>
          <dl>
            <div>
              <dt>{axisLabel(context.primary_axis)}</dt>
              <dd>
                {axisDefinitions[context.primary_axis] ??
                  "Definition unavailable."}
              </dd>
            </div>
            {context.secondary_axes?.map((axis) => (
              <div key={axis}>
                <dt>{axisLabel(axis)}</dt>
                <dd>{axisDefinitions[axis] ?? "Definition unavailable."}</dd>
              </div>
            ))}
          </dl>
          {context.verified_findings.length > 0 && (
            <section>
              <h5>Independently verified findings</h5>
              <ul>
                {context.verified_findings.map((finding, index) => (
                  <li key={`${finding.axis}-${index}`}>
                    <strong>{axisLabel(finding.axis)}</strong>
                    {axisDefinitions[finding.axis] && (
                      <span> · {axisDefinitions[finding.axis]}</span>
                    )}
                    {": "}
                    {finding.finding}
                    <small className="family-finding-references">
                      Evidence references: {finding.evidence.join(", ")}
                    </small>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {context.incidental_challenges.length > 0 && (
            <section>
              <h5>Incidental challenges</h5>
              <ul>
                {context.incidental_challenges.map((challenge) => (
                  <li key={challenge}>{challenge}</li>
                ))}
              </ul>
            </section>
          )}
        </details>
      </div>

      <dl className="family-axis-list">
        <div>
          <dt>Primary difficulty axis</dt>
          <dd>{axisLabel(context.primary_axis)}</dd>
        </div>
        <div>
          <dt>Secondary difficulty axes (declared)</dt>
          <dd>
            {context.secondary_axes === null
              ? "Not recorded"
              : context.secondary_axes.length === 0
                ? "None declared"
                : context.secondary_axes.map(axisLabel).join(" · ")}
          </dd>
        </div>
      </dl>
    </section>
  );
}

function axisLabel(axis: string) {
  return axis
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
