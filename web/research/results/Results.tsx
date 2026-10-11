import { useCallback } from "react";
import { experiment } from "../shared/api";
import { useRead } from "../shared/useRead";
import { mode, ReadState, RecordedDetails } from "../shared/presentation";
import { Investigation } from "./Investigation";
import { Overview } from "./Overview";
import { Execution } from "./Execution";

export function Results({
  id,
  params,
  historyLink,
  executable = false,
}: {
  id: string;
  params: URLSearchParams;
  historyLink: string;
  executable?: boolean;
}) {
  const load = useCallback(
    (signal: AbortSignal) => experiment(id, signal),
    [id],
  );
  const { data, error, retry } = useRead(load);
  const link = (changes: Record<string, string>) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => next.set(key, value));
    return `#${next}`;
  };
  const view = params.get("view") ?? "overview";
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
      <a className="breadcrumb" href={historyLink}>
        Back to experiments
      </a>
      <div className="experiment-heading">
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
      <nav className="result-tabs" aria-label="Experiment views">
        {[
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
