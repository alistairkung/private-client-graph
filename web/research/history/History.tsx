import { useCallback, useState } from "react";
import { history } from "../shared/api";
import { useRead } from "../shared/useRead";
import { mode, ReadState } from "../shared/presentation";

export function History({ params }: { params: URLSearchParams }) {
  const query = params.toString();
  const load = useCallback(
    (signal: AbortSignal) => history(new URLSearchParams(query), signal),
    [query],
  );
  const { data, error, retry } = useRead(load);
  const [selected, setSelected] = useState<Record<string, string>>({});
  const entries = Object.entries(selected);
  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    value ? next.set(key, value) : next.delete(key);
    next.delete("offset");
    window.location.hash = next.toString();
  };
  const page = (offset: number) => {
    const next = new URLSearchParams(params);
    next.set("offset", String(offset));
    return `#${next}`;
  };
  return (
    <>
      <h1>Experiments</h1>
      <p className="lede">
        Trace a result from the experiment to its exact supporting Evidence.
      </p>
      <form
        className="history-filters"
        onSubmit={(event) => {
          event.preventDefault();
          update("q", String(new FormData(event.currentTarget).get("q") ?? ""));
        }}
      >
        <label>
          Search experiments
          <input
            name="q"
            key={params.get("q")}
            defaultValue={params.get("q") ?? ""}
            placeholder="Identity, case, model or configuration"
            type="search"
          />
        </label>
        <button type="submit">Search</button>
        <label>
          Execution status
          <select
            value={params.get("lifecycle") ?? ""}
            onChange={(event) => update("lifecycle", event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="complete">Complete</option>
            <option value="incomplete">Incomplete</option>
            <option value="failed">Failed</option>
            <option value="unavailable">Unavailable</option>
            {["frozen", "running", "stopping", "stopped", "interrupted"].map(
              (state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ),
            )}
          </select>
        </label>
        <label>
          Execution mode
          <select
            value={params.get("kind") ?? ""}
            onChange={(event) => update("kind", event.target.value)}
          >
            <option value="">All modes</option>
            <option value="replay">Saved replay</option>
            <option value="demonstration">Recorded demonstration</option>
            <option value="task_b_pilot">Development pilot</option>
            <option value="task_a_diagnostic">Development diagnostic</option>
          </select>
        </label>
        <label>
          Artifact integrity
          <select
            value={params.get("integrity") ?? ""}
            onChange={(event) => update("integrity", event.target.value)}
          >
            <option value="">All artifacts</option>
            {["verified", "missing", "corrupt", "unsupported"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
      </form>
      {entries.length > 0 && (
        <div className="comparison-selection">
          <p>Selected: {entries.map(([, name]) => name).join(" and ")}</p>
          {entries.length === 2 ? (
            <a
              className="button"
              href={`#${params}&${new URLSearchParams({ left: entries[0][0], right: entries[1][0] })}`}
            >
              Compare selected experiments
            </a>
          ) : (
            <p>Select one more experiment to compare.</p>
          )}
          <button onClick={() => setSelected({})}>Clear selection</button>
        </div>
      )}
      {!data ? (
        <ReadState error={error} retry={retry} />
      ) : data.total === 0 ? (
        <section className="empty">
          <h2>
            {query ? "No matching experiments" : "No experiments indexed"}
          </h2>
          <p>Retained experiment artifacts appear here after indexing.</p>
          {query && <a href="#">Clear filters</a>}
        </section>
      ) : (
        <>
          <p role="status">
            {data.total} experiments · {data.offset + 1}–
            {Math.min(data.offset + data.limit, data.total)} shown
          </p>
          <div className="table-scroll">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Compare</th>
                  <th>Experiment / date</th>
                  <th>Cases / configuration</th>
                  <th>Model / mode</th>
                  <th>Status / integrity</th>
                  <th>Scored / planned</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Compare ${item.artifact_path}`}
                        checked={Boolean(selected[item.id])}
                        disabled={
                          (!selected[item.id] && entries.length === 2) ||
                          item.integrity !== "verified" ||
                          item.freshness !== "current"
                        }
                        onChange={(event) =>
                          setSelected((current) => {
                            const next = { ...current };
                            event.target.checked
                              ? (next[item.id] = item.artifact_path)
                              : delete next[item.id];
                            return next;
                          })
                        }
                      />
                    </td>
                    <td>
                      <a href={`#${params}&experiment=${item.id}`}>
                        {item.artifact_path}
                      </a>
                      <small>
                        {item.created_at
                          ? new Date(item.created_at).toLocaleString()
                          : "Date unavailable"}
                      </small>
                    </td>
                    <td>
                      {item.cases.join(", ") || "Unavailable"}
                      <small>
                        {item.configurations.length
                          ? item.configurations
                              .map((value) =>
                                value === "noop"
                                  ? "No resolution"
                                  : "Generative resolution",
                              )
                              .join(" / ")
                          : "Configuration unavailable"}
                      </small>
                    </td>
                    <td>
                      {item.model ?? "Unavailable"}
                      <small>{mode(item.kind)}</small>
                    </td>
                    <td>
                      <span
                        className={
                          item.lifecycle === "failed" ||
                          item.integrity !== "verified"
                            ? "error-text"
                            : ""
                        }
                      >
                        {item.lifecycle}
                      </span>
                      <small>
                        {item.integrity} · {item.freshness}
                      </small>
                    </td>
                    <td className="numeric">
                      {item.scored ?? "Unavailable"} /{" "}
                      {item.planned ?? "Unavailable"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <nav aria-label="History pages" className="pagination">
            {data.offset > 0 && (
              <a href={page(Math.max(0, data.offset - data.limit))}>
                Previous page
              </a>
            )}
            {data.offset + data.limit < data.total && (
              <a href={page(data.offset + data.limit)}>Next page</a>
            )}
          </nav>
        </>
      )}
    </>
  );
}
