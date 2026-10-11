import { useRef, useState } from "react";
import type { CaseMetadata } from "../shared/contracts";
export function CasePicker({
  cases,
  selected,
  update,
  disabled,
}: {
  cases: CaseMetadata[];
  selected: string[];
  update: (ids: string[]) => void;
  disabled: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [pending, setPending] = useState(selected);
  return (
    <div className="case-picker">
      <span>{selected.length} benchmark inputs selected</span>
      <button
        type="button"
        className="secondary"
        disabled={disabled}
        onClick={() => {
          setPending(selected);
          dialog.current?.showModal();
        }}
      >
        Choose cases
      </button>
      <dialog ref={dialog} aria-labelledby="case-picker-title">
        <h2 id="case-picker-title">Benchmark cases</h2>
        <div className="run-actions">
          <button
            type="button"
            onClick={() =>
              setPending(
                cases
                  .filter((item) => item.kind === "benchmark")
                  .map((item) => item.id),
              )
            }
          >
            All benchmark cases
          </button>
          <button type="button" onClick={() => setPending([])}>
            Clear selection
          </button>
        </div>
        {cases.map((item) => (
          <label className="input-option" key={item.id}>
            <input
              type="checkbox"
              checked={pending.includes(item.id)}
              onChange={(e) =>
                setPending(
                  e.target.checked
                    ? [...pending, item.id]
                    : pending.filter((id) => id !== item.id),
                )
              }
            />
            <span>
              <strong>{item.name}</strong>
              <span className="case-description">
                {item.description ?? "Description unavailable"}
              </span>
              <small>
                {item.case_id} · {item.id} · {item.kind}
              </small>
              <span className="case-description">{item.fixture_name}</span>
              <small>
                {item.fixture_description ?? "Fixture description unavailable"}
              </small>
            </span>
          </label>
        ))}
        <div className="run-actions">
          <button
            type="button"
            disabled={!pending.length}
            onClick={() => {
              update(pending);
              dialog.current?.close();
            }}
          >
            Apply cases
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => dialog.current?.close()}
          >
            Cancel
          </button>
        </div>
      </dialog>
    </div>
  );
}
