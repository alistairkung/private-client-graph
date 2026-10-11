import { useCallback, useState } from "react";
import { history } from "../shared/api";
import { useRead } from "../shared/useRead";
import { ReadState } from "../shared/presentation";

export function Sidebar({
  selected,
  executable,
  refreshKey,
  newExperiment,
}: {
  selected: string | null;
  executable: boolean;
  refreshKey: string;
  newExperiment: () => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const load = useCallback(
    (signal: AbortSignal) => {
      void refreshKey;
      return history(new URLSearchParams({ q: query, limit: "12" }), signal);
    },
    [query, refreshKey],
  );
  const { data, error, retry } = useRead(load);
  return (
    <>
      <button
        className="sidebar-toggle"
        aria-expanded={open}
        aria-controls="experiment-sidebar"
        onClick={() => setOpen(!open)}
      >
        Experiments
      </button>
      <aside
        className={`experiment-sidebar ${open ? "open" : ""}`}
        id="experiment-sidebar"
      >
        <strong>Private Client Graph</strong>
        <p>Research Workbench</p>
        <button className="sidebar-toggle" onClick={() => setOpen(false)}>
          Close experiments
        </button>
        {executable && (
          <a
            className="new-experiment"
            href="#new=1"
            onClick={() => {
              newExperiment();
              setOpen(false);
            }}
          >
            New experiment
          </a>
        )}
        <label>
          Search recent experiments
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <h2>Recent experiments</h2>
        {!data ? (
          <ReadState error={error} retry={retry} />
        ) : (
          <nav aria-label="Recent experiments">
            {data.items.map((item) => (
              <a
                key={item.id}
                href={`#experiment=${item.id}`}
                aria-current={
                  selected === item.id || selected === item.artifact_path
                    ? "page"
                    : undefined
                }
                onClick={() => setOpen(false)}
              >
                <strong>{item.artifact_path}</strong>
                <small>
                  {item.lifecycle} · {item.scored ?? "?"}/{item.planned ?? "?"}{" "}
                  scored
                </small>
              </a>
            ))}
            {!data.items.length && <p>No matching experiments.</p>}
          </nav>
        )}
        <a href="#browse=1" onClick={() => setOpen(false)}>
          Browse all experiments
        </a>
        <p className="muted">
          Local · Synthetic
          <br />
          Artifacts retain the record.
        </p>
      </aside>
    </>
  );
}
