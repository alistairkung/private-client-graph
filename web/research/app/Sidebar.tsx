import { useCallback, useEffect, useRef, useState } from "react";
import { listWorkspaces } from "../workspace/api";
import { useRead } from "../shared/useRead";
import { ReadState } from "../shared/presentation";

export function Sidebar({
  selected,
  executable,
  revision,
  collapsed,
  toggle,
  saving,
}: {
  selected: string | null;
  executable: boolean;
  revision: number;
  collapsed: boolean;
  toggle: () => void;
  saving: boolean;
}) {
  const [query, setQuery] = useState("");
  const [narrow, setNarrow] = useState(
    () => matchMedia("(width < 760px)").matches,
  );
  const [open, setOpen] = useState(false);
  const drawer = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const load = useCallback(
    (signal: AbortSignal) => {
      void revision;
      return listWorkspaces(signal);
    },
    [revision],
  );
  const { data, error, retry } = useRead(load);
  function close() {
    drawer.current?.close();
    setOpen(false);
    trigger.current?.focus();
  }
  useEffect(() => {
    const media = matchMedia("(width < 760px)");
    const change = () => {
      drawer.current?.close();
      setOpen(false);
      setNarrow(media.matches);
    };
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  const content = (
    <>
      <strong>Private Client Graph</strong>
      <p>Research Workbench</p>
      {narrow && (
        <button className="secondary" onClick={close}>
          Close experiments
        </button>
      )}
      {executable && (
        <a
          className="new-experiment"
          href="#new=1"
          onClick={(event) => {
            if (saving) {
              event.preventDefault();
              return;
            }
            if (narrow) close();
          }}
        >
          New experiment
        </a>
      )}
      {saving && (
        <p role="status">
          Save or correct the draft before switching experiments.
        </p>
      )}
      <label>
        Find an experiment
        <input
          type="search"
          placeholder="Search workspaces"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </label>
      {!data ? (
        <ReadState error={error} retry={retry} />
      ) : (
        <nav aria-label="Experiments">
          {data.items
            .filter((item) =>
              `${item.name} ${item.hypothesis ?? ""} ${item.id}`
                .toLowerCase()
                .includes(query.toLowerCase()),
            )
            .map((item) => (
              <a
                key={item.id}
                href={`#workspace=${item.id}`}
                aria-current={selected === item.id ? "page" : undefined}
                onClick={(event) => {
                  if (saving) {
                    event.preventDefault();
                    return;
                  }
                  if (narrow) close();
                }}
              >
                <strong>{item.name}</strong>
                <small>
                  {item.run_ids.length} Runs · {item.integrity}
                </small>
                {item.hypothesis && <small>{item.hypothesis}</small>}
                {item.reason && <small>{item.reason}</small>}
              </a>
            ))}
          {!data.items.length && <p>No experiments yet.</p>}
        </nav>
      )}
      <a
        href="#browse=1"
        onClick={(event) => {
          if (saving) {
            event.preventDefault();
            return;
          }
          if (narrow) close();
        }}
      >
        Legacy study history
      </a>
      <p className="muted">Local · Synthetic research</p>
    </>
  );
  return (
    <>
      <button
        className="workspace-sidebar-toggle secondary"
        ref={trigger}
        aria-expanded={narrow ? open : !collapsed}
        aria-controls="experiment-sidebar"
        onClick={() => {
          if (narrow) {
            if (open) close();
            else {
              drawer.current?.showModal();
              setOpen(true);
            }
          } else toggle();
        }}
      >
        {narrow
          ? "Experiments"
          : collapsed
            ? "Expand experiments"
            : "Collapse experiments"}
      </button>
      {narrow ? (
        <dialog
          id="experiment-sidebar"
          ref={drawer}
          className="experiment-drawer"
          aria-label="Experiments"
          onKeyDown={(event) => {
            if (event.key !== "Tab") return;
            const controls = Array.from(
              event.currentTarget.querySelectorAll<HTMLElement>(
                "button:not(:disabled), a[href], input:not(:disabled)",
              ),
            );
            const first = controls[0],
              last = controls.at(-1);
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              last?.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first?.focus();
            }
          }}
          onClose={() => {
            setOpen(false);
            trigger.current?.focus();
          }}
        >
          {content}
        </dialog>
      ) : (
        <aside
          id="experiment-sidebar"
          className="experiment-sidebar"
          hidden={collapsed}
        >
          {content}
        </aside>
      )}
    </>
  );
}
