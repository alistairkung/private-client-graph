import type { ExperimentDetail, Observation } from "../shared/contracts";
import { configuration, number, RecordedDetails } from "../shared/presentation";
import { EvidenceInspector } from "./EvidenceInspector";

type Link = (changes: Record<string, string>) => string;
const outcomes = [
  ["all", "All relationships"],
  ["missing", "Missing"],
  ["extra", "Extra"],
  ["provenance_failure", "Provenance failures"],
  ["matched", "Matched"],
];

export function Investigation({
  data,
  params,
  link,
}: {
  data: ExperimentDetail;
  params: URLSearchParams;
  link: Link;
}) {
  const caseFilter = params.get("case_outcome") ?? "all";
  const sample =
    data.samples.find((item) => item.id === params.get("sample")) ??
    data.samples[0];
  if (!sample) return <p>No frozen samples are available for inspection.</p>;
  const selected =
    sample.observations.find((item) => item.id === params.get("observation")) ??
    sample.observations[0];
  const outcome = params.get("outcome") ?? "all";
  const relationship = selected.relationships.find(
    (item) => item.id === params.get("relationship"),
  );
  const relationships = selected.relationships.filter(
    (item) => outcome === "all" || item.outcome === outcome,
  );
  return (
    <div className="investigation">
      <aside className="case-navigator" id="cases">
        <details open>
          <summary>Case navigator</summary>
          <label>
            Samples with outcome
            <select
              value={caseFilter}
              onChange={(event) => {
                window.location.hash = link({
                  case_outcome: event.target.value,
                });
              }}
            >
              {outcomes.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <nav aria-label="Cases and extraction samples">
            {["authored", "historical", "fresh"].map((cohort) => (
              <section key={cohort}>
                <h3>{cohort}</h3>
                {data.samples
                  .filter(
                    (item) =>
                      item.cohort === cohort &&
                      (caseFilter === "all" ||
                        item.outcome_filters.includes(caseFilter)),
                  )
                  .map((item) => (
                    <a
                      key={item.id}
                      aria-current={sample.id === item.id ? "true" : undefined}
                      href={link({
                        sample: item.id,
                        observation: "noop-0",
                        relationship: "",
                        outcome: "all",
                      })}
                    >
                      <strong>{item.case_id}</strong>
                      <span>{item.id}</span>
                      <small>
                        {item.scored} / {item.planned} treatment scored
                      </small>
                    </a>
                  ))}
              </section>
            ))}
          </nav>
        </details>
      </aside>
      <section
        className="relationship-workspace"
        id="relationships"
        aria-label="Relationship investigation"
        tabIndex={-1}
      >
        <a
          className="mobile-back"
          href="#cases"
          onClick={(event) => {
            event.preventDefault();
            const target =
              document.querySelector<HTMLElement>("#cases summary");
            target?.focus();
            target?.scrollIntoView({ block: "start" });
          }}
        >
          Back to cases
        </a>
        <h2>{sample.case_id}</h2>
        <p>
          {sample.id} · {sample.cohort}
        </p>
        <label>
          Observation
          <select
            value={selected.id}
            onChange={(event) => {
              window.location.hash = link({
                observation: event.target.value,
                relationship: "",
              });
            }}
          >
            {sample.observations.map((item) => (
              <option key={item.id} value={item.id}>
                {configuration(item.configuration)}
                {item.repetition
                  ? ` · Repetition ${item.repetition}`
                  : ""} · {item.status}
              </option>
            ))}
          </select>
        </label>
        <MetricTable
          observations={sample.observations}
          selected={selected}
          link={link}
        />
        <p role="status">
          {configuration(selected.configuration)} · {selected.status}
          {selected.stage && ` · ${selected.stage} stage`}
          {selected.error_type && ` · ${selected.error_type}`}
        </p>
        <nav className="outcome-filters" aria-label="Relationship outcomes">
          {outcomes.map(([value, label]) => (
            <a
              key={value}
              aria-current={value === outcome ? "true" : undefined}
              href={link({ outcome: value, relationship: "" })}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="relationship-list">
          {relationships.map((item) => (
            <a
              key={item.id}
              aria-current={relationship?.id === item.id ? "true" : undefined}
              href={link({ relationship: item.id })}
            >
              <span className={item.outcome !== "matched" ? "error-text" : ""}>
                {outcomes.find(([value]) => value === item.outcome)?.[1]}
              </span>
              <strong>
                {item.edge[0]}{" "}
                <span className="relationship-type">{item.edge[1]}</span>{" "}
                {item.edge[2]}
              </strong>
              <small>{configuration(selected.configuration)}</small>
            </a>
          ))}
        </div>
        {relationships.length === 0 && (
          <p>
            {selected.evaluation
              ? "No relationships in this filter."
              : "Evaluation unavailable for this observation."}
          </p>
        )}
        {selected.identity ? (
          <RecordedDetails
            title="Identity diagnostics"
            value={selected.identity}
          />
        ) : (
          <p className="muted">
            Identity diagnostics: Unavailable. {selected.identity_reason}
          </p>
        )}
      </section>
      <EvidenceInspector
        key={`${sample.id}-${selected.id}-${relationship?.id}`}
        relationship={relationship}
        source={sample.source}
      />
    </div>
  );
}

function MetricTable({
  observations,
  selected,
  link,
}: {
  observations: Observation[];
  selected: Observation;
  link: Link;
}) {
  const baseline = observations[0];
  const treatment =
    selected.configuration === "noop" ? observations[1] : selected;
  return (
    <div className="table-scroll">
      <table className="paired-metrics">
        <caption>Paired observation metrics</caption>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Baseline</th>
            <th>Treatment {treatment?.repetition}</th>
          </tr>
        </thead>
        <tbody>
          {(["precision", "recall", "f1", "provenance_accuracy"] as const).map(
            (metric) => (
              <tr key={metric}>
                <th>{metric.replaceAll("_", " ")}</th>
                <td>{number(baseline.evaluation?.[metric])}</td>
                <td>{number(treatment?.evaluation?.[metric])}</td>
              </tr>
            ),
          )}
          {(
            [
              ["fn", "Missing", "missing"],
              ["fp", "Extra", "extra"],
              [
                "provenance_failed",
                "Provenance failures",
                "provenance_failure",
              ],
            ] as const
          ).map(([metric, label, filter]) => (
            <tr key={metric}>
              <th>{label}</th>
              {[baseline, treatment].map((row, index) => (
                <td key={index}>
                  {row?.evaluation ? (
                    <a
                      href={link({
                        observation: row.id,
                        outcome: filter,
                        relationship: "",
                      })}
                      aria-label={`${index === 0 ? "Baseline" : "Treatment"} ${label}: ${row.evaluation[metric]}`}
                    >
                      {row.evaluation[metric]}
                    </a>
                  ) : (
                    "Unavailable"
                  )}
                </td>
              ))}
            </tr>
          ))}
          <tr>
            <th>F1 delta</th>
            <td>—</td>
            <td>{number(treatment?.delta_f1)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
