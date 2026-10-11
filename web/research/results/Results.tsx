import { useCallback } from "react";
import { experiment } from "../shared/api";
import { useRead } from "../shared/useRead";
import { mode, ReadState, RecordedDetails } from "../shared/presentation";
import { Investigation } from "./Investigation";
import { Overview } from "./Overview";
import { Execution } from "./Execution";

import { Pipeline } from "../configuration/Pipeline";
import { UsageSummary } from "./UsageSummary";
import { ComparisonBench } from "./ComparisonBench";

export function Results({
  id,
  params,
  historyLink,
  executable = false,
  embedded = false,
  refresh = 0,
}: {
  id: string;
  params: URLSearchParams;
  historyLink: string;
  executable?: boolean;
  embedded?: boolean;
  refresh?: number;
}) {
  const load = useCallback(
    (signal: AbortSignal) => experiment(id, signal),
    [id, refresh],
  );
  const { data, error, retry } = useRead(load);
  const link = (changes: Record<string, string>) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => next.set(key, value));
    return `#${next}`;
  };
  const view = params.get("view") ?? "bench";
  if (!data)
    return (
      <>
        <a href={historyLink}>Back to experiments</a>
        <ReadState error={error} retry={retry} />
      </>
    );
  const { history } = data;
  return (
    <>
      <a className="breadcrumb" href={historyLink} hidden={embedded}>
        Back to experiments
      </a>
      <div className="experiment-heading" hidden={embedded}>
        <h1>{history.artifact_path}</h1>
        <p>
          {mode(history.kind)} · {history.lifecycle} ·{" "}
          {history.scored ?? "Unavailable"} / {history.planned ?? "Unavailable"}{" "}
          observations scored
        </p>
        <p>
          {history.cohorts.join(" / ")} · {history.model ?? "Model unavailable"}
        </p>
      </div>
      {data.configuration.execution_mode === "replay" && (
        <p className="notice">
          Saved replay · No resolution · No provider calls.
        </p>
      )}
      {executable &&
        [2, 3].includes(Number(data.configuration.plan_version)) && (
          <p>
            <a href={`#plan=${history.artifact_path}`}>
              Execution status and controls
            </a>
          </p>
        )}
      {history.kind === "demonstration" &&
        data.configuration.execution_mode !== "replay" && (
          <p className="notice">
            Recorded provider responses. This demonstration is not a live
            quality measurement.
          </p>
        )}
      {history.lifecycle === "incomplete" && (
        <p className="notice">
          Incomplete experiment. Unattempted and uncertain observations remain
          visible. Historical imports cannot resume execution.
        </p>
      )}
      {history.lifecycle === "failed" && (
        <p className="notice">
          This experiment contains failed or unavailable observations. Inspect
          the recorded stages; missing scores are not zero.
        </p>
      )}
      <details>
        <summary>
          Artifact integrity and provenance · {history.integrity} ·{" "}
          {history.freshness}
        </summary>
        <dl>
          <dt>Experiment identity</dt>
          <dd>{history.experiment_id ?? "Unavailable"}</dd>
          <dt>Artifact / API version</dt>
          <dd>
            {history.artifact_version ?? "Unavailable"} / {data.api_version}
          </dd>
          <dt>Indexed digest</dt>
          <dd>{history.digest}</dd>
          <dt>Indexed at</dt>
          <dd>{history.indexed_at}</dd>
        </dl>
        <RecordedDetails
          title="Recorded configuration"
          value={data.configuration}
        />
        <RecordedDetails
          title="Code, dependencies and prompts"
          value={data.provenance}
        />
      </details>
      {!embedded &&
        history.integrity === "verified" &&
        history.freshness === "current" && (
          <>
            <Pipeline
              frozen={{
                resolver: history.configurations.includes(
                  "generative_full_source",
                ),
                input: `${data.samples.length} retained samples · ${history.cohorts.join(" / ")}`,
                model: history.model ?? "Unavailable",
                repetitions: String(
                  data.configuration.repetitions ?? "Unavailable",
                ),
              }}
            />
            <section className="historical-console execution-bench">
              <div className="run-status">
                <h2>Execution · {history.lifecycle}</h2>
                <p>
                  {history.scored ?? "Unavailable"} /{" "}
                  {history.planned ?? "Unavailable"} observations scored ·
                  Read-only retained results
                </p>
                <p>
                  {String(data.operations.valid_attempts ?? "Unavailable")}{" "}
                  valid attempts ·{" "}
                  {String(
                    data.operations.provider_failed_attempts ?? "Unavailable",
                  )}{" "}
                  provider failures ·{" "}
                  {String(data.operations.uncertain_attempts ?? "Unavailable")}{" "}
                  uncertain
                </p>
              </div>
              <div className="execution-review">
                <UsageSummary data={data} />
              </div>
            </section>
          </>
        )}
      {embedded &&
        history.integrity === "verified" &&
        history.freshness === "current" && (
          <details>
            <summary>Recorded attempt accounting and provider usage</summary>
            <p>
              {String(data.operations.valid_attempts ?? "Unavailable")} valid
              attempts ·{" "}
              {String(
                data.operations.provider_failed_attempts ?? "Unavailable",
              )}{" "}
              provider failures ·{" "}
              {String(data.operations.uncertain_attempts ?? "Unavailable")}{" "}
              uncertain
            </p>
            <UsageSummary data={data} />
          </details>
        )}
      <nav className="result-tabs" aria-label="Experiment views">
        {[
          ["bench", "Comparison bench"],
          ["overview", "Overview"],
          ["investigate", "Investigate"],
          ["execution", "Execution & artifacts"],
        ].map(([value, label]) => (
          <a
            key={value}
            href={link({ view: value })}
            aria-current={view === value ? "page" : undefined}
          >
            {label}
          </a>
        ))}
      </nav>
      {history.integrity !== "verified" || history.freshness !== "current" ? (
        <section role="alert">
          <h2>Artifact cannot be inspected</h2>
          <p>{history.integrity_reason}</p>
        </section>
      ) : view === "bench" ? (
        <ComparisonBench data={data} params={params} link={link} />
      ) : view === "investigate" ? (
        <Investigation data={data} params={params} link={link} />
      ) : view === "execution" ? (
        <Execution data={data} />
      ) : (
        <Overview data={data} link={link} />
      )}
    </>
  );
}
