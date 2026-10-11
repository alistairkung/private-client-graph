import { useRef, useState } from "react";
import type { Capabilities, Proposal } from "../shared/contracts";

export function InputSelection({
  proposal,
  capabilities,
  update,
  busy,
}: {
  proposal: Proposal;
  capabilities: Capabilities;
  update: (changes: Partial<Proposal>) => void;
  busy: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [selected, setSelected] = useState(proposal.input_ids);
  const [query, setQuery] = useState("");
  const inputs = capabilities.inputs.filter(
    (input) =>
      proposal.input_mode === "saved" ||
      input.id === capabilities.fresh_input_id,
  );
  return (
    <div className="benchmark-selection">
      <span>
        <strong>{proposal.input_ids.length} benchmark inputs selected</strong>
        <small>Repository-owned synthetic inputs · {proposal.input_mode}</small>
      </span>
      <button
        type="button"
        disabled={busy}
        onClick={() => {
          setSelected(proposal.input_ids);
          setQuery("");
          dialog.current?.showModal();
        }}
      >
        Customize inputs
      </button>
      <dialog ref={dialog} aria-labelledby="input-dialog-title">
        <h2 id="input-dialog-title">Select benchmark inputs</h2>
        <label>
          Find inputs
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <p>{selected.length} selected</p>
        <button
          type="button"
          onClick={() => setSelected(inputs.map((i) => i.id))}
        >
          Select all
        </button>{" "}
        <button
          type="button"
          disabled={proposal.input_mode === "fresh"}
          onClick={() => setSelected([])}
        >
          Clear selection
        </button>
        {inputs
          .filter((i) =>
            `${i.id} ${i.case_id} ${i.cohort}`
              .toLowerCase()
              .includes(query.toLowerCase()),
          )
          .map((input) => (
            <label className="input-option" key={input.id}>
              <input
                type="checkbox"
                disabled={proposal.input_mode === "fresh"}
                checked={selected.includes(input.id)}
                onChange={(e) =>
                  setSelected(
                    e.target.checked
                      ? [...selected, input.id]
                      : selected.filter((id) => id !== input.id),
                  )
                }
              />
              <span>
                {input.id}
                <small>
                  {input.case_id} · {input.cohort}
                </small>
              </span>
            </label>
          ))}
        <div className="run-actions">
          <button type="button" onClick={() => dialog.current?.close()}>
            Cancel
          </button>
          <button
            type="button"
            disabled={!selected.length}
            onClick={() => {
              update({ input_ids: selected });
              dialog.current?.close();
            }}
          >
            Apply inputs
          </button>
        </div>
      </dialog>
    </div>
  );
}
