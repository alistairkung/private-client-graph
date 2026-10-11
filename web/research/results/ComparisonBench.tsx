import type { ExperimentDetail, Observation } from "../shared/contracts";
import { number } from "../shared/presentation";
import { EvidenceInspector } from "./EvidenceInspector";

type Link = (changes: Record<string, string>) => string;
export function ComparisonBench({
  data,
  params,
  link,
}: {
  data: ExperimentDetail;
  params: URLSearchParams;
  link: Link;
}) {
  const sample =
    data.samples.find((s) => s.id === params.get("sample")) ?? data.samples[0];
  if (!sample)
    return (
      <p>
        No retained observations yet. Evaluation will appear as results become
        available.
      </p>
    );
  const baseline = sample.observations.find((o) => o.configuration === "noop");
  const treatments = sample.observations.filter(
    (o) => o.configuration !== "noop",
  );
  const treatment =
    treatments.find((o) => o.id === params.get("treatment")) ??
    treatments.find((o) => o.id === params.get("observation")) ??
    treatments[0];
  const selected =
    sample.observations.find((o) => o.id === params.get("observation")) ??
    baseline;
  const outcome = params.get("outcome") ?? "missing";
  const rows =
    selected?.relationships.filter(
      (r) => outcome === "all" || r.outcome === outcome,
    ) ?? [];
  const relationship = rows.find((r) => r.id === params.get("relationship"));
  const pair: [string, Observation | undefined][] = [
    ["Baseline", baseline],
    ["Treatment", treatment],
  ];
  return (
    <section className="comparison-bench" aria-label="Relationship evaluation">
      <h2>Relationship evaluation</h2>
      <p>
        {data.history.scored ?? "Unavailable"} /{" "}
        {data.history.planned ?? "Unavailable"} observations scored ·{" "}
        {data.history.lifecycle === "complete"
          ? "Retained results"
          : "Partial coverage · Not final"}
      </p>
      <div className="bench-selectors">
        <label>
          Input / cohort
          <select
            value={sample.id}
            onChange={(e) => {
              window.location.hash = link({
                sample: e.target.value,
                observation: "",
                treatment: "",
                relationship: "",
              });
            }}
          >
            {data.samples.map((s) => (
              <option key={s.id} value={s.id}>
                {s.id} · {s.cohort}
              </option>
            ))}
          </select>
        </label>
        <label>
          Treatment repetition
          <select
            value={treatment?.id ?? ""}
            disabled={!treatments.length}
            onChange={(e) => {
              window.location.hash = link({
                treatment: e.target.value,
                observation: e.target.value,
                relationship: "",
              });
            }}
          >
            {!treatments.length && <option value="">No treatment</option>}
            {treatments.map((o) => (
              <option key={o.id} value={o.id}>
                Repetition {o.repetition} · {o.status}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="muted">
        Metrics below apply to this input and repetition. No true-negative
        category is defined.
      </p>
      <div className="bench-columns">
        <div className="bench-comparison">
          <div className="table-scroll">
            <table className="outcome-matrix">
              <caption>Relationship outcome matrix</caption>
              <thead>
                <tr>
                  <th>Configuration</th>
                  <th>Matched · TP</th>
                  <th>Extra · FP</th>
                  <th>Missing · FN</th>
                </tr>
              </thead>
              <tbody>
                {pair.map(([label, observation]) => (
                  <tr key={label}>
                    <th>
                      {label}
                      <small>
                        {label === "Baseline" ? "No resolution" : "Generative"}
                      </small>
                    </th>
                    {(
                      [
                        ["tp", "matched"],
                        ["fp", "extra"],
                        ["fn", "missing"],
                      ] as const
                    ).map(([metric, filter]) => (
                      <td key={metric}>
                        {observation?.evaluation ? (
                          <a
                            aria-label={`${label} ${filter}: ${observation.evaluation[metric]}`}
                            aria-current={
                              selected?.id === observation.id &&
                              outcome === filter
                                ? "true"
                                : undefined
                            }
                            href={link({
                              observation: observation.id,
                              outcome: filter,
                              relationship: "",
                              treatment: treatment?.id ?? "",
                            })}
                          >
                            {observation.evaluation[metric]}
                            <small>Inspect {filter}</small>
                          </a>
                        ) : (
                          <span>Unavailable</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <table className="bench-metrics">
              <caption>Paired observation metrics</caption>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Baseline</th>
                  <th>Treatment</th>
                </tr>
              </thead>
              <tbody>
                {(
                  ["precision", "recall", "f1", "provenance_accuracy"] as const
                ).map((metric) => (
                  <tr key={metric}>
                    <th>{metric.replaceAll("_", " ")}</th>
                    <td>{number(baseline?.evaluation?.[metric])}</td>
                    <td>{number(treatment?.evaluation?.[metric])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted">
            Provenance accuracy measures support for matched relationships, not
            overall classification accuracy.
          </p>
          <details>
            <summary>Repetition variability</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Repetition</th>
                    <th>F1</th>
                    <th>Δ vs baseline</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {treatments.map((o) => (
                    <tr key={o.id}>
                      <th>
                        <a
                          href={link({
                            treatment: o.id,
                            observation: o.id,
                            relationship: "",
                          })}
                        >
                          {o.repetition}
                        </a>
                      </th>
                      <td>{number(o.evaluation?.f1)}</td>
                      <td>{number(o.delta_f1)}</td>
                      <td>{o.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
        <div className="bench-inspection" id="relationships" tabIndex={-1}>
          <h3>Relationship inspection</h3>
          <p>
            {selected?.configuration ?? "Unavailable"} ·{" "}
            {selected?.status ?? "No observation"}
            {selected?.error_type && ` · ${selected.error_type}`}
          </p>
          <label>
            Relationship category
            <select
              value={outcome}
              onChange={(e) => {
                window.location.hash = link({
                  outcome: e.target.value,
                  relationship: "",
                });
              }}
            >
              {["all", "matched", "extra", "missing", "provenance_failure"].map(
                (v) => (
                  <option key={v} value={v}>
                    {v.replaceAll("_", " ")}
                  </option>
                ),
              )}
            </select>
          </label>
          <div className="relationship-list">
            {rows.map((r) => (
              <a
                key={r.id}
                aria-current={relationship?.id === r.id ? "true" : undefined}
                href={link({ relationship: r.id })}
              >
                <strong>
                  {r.edge[0]} {r.edge[1].replaceAll("_", " ")} {r.edge[2]}
                </strong>
              </a>
            ))}
          </div>
          {!rows.length && (
            <p>
              {selected?.evaluation
                ? "No relationships in this category."
                : "Evaluation unavailable for this observation."}
            </p>
          )}
          <EvidenceInspector
            key={`${sample.id}-${selected?.id}-${relationship?.id}`}
            relationship={relationship}
            source={sample.source}
          />
        </div>
      </div>
    </section>
  );
}
