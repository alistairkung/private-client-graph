import { useEffect, useState } from "react";
import { getMatters } from "./api";
import type { MatterSummary } from "./types";

type CollectionState =
  | { status: "loading" }
  | { status: "failed" }
  | { status: "ready"; matters: MatterSummary[] };

export function MatterLedger() {
  const [state, setState] = useState<CollectionState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    getMatters().then(
      matters => { if (active) setState({ status: "ready", matters }); },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, []);

  return (
    <table className="matter-register" aria-label="Matters">
      <thead>
        <tr><th scope="col">Matter reference</th><th scope="col">Matter</th></tr>
      </thead>
      <tbody>
        {state.status === "ready" && state.matters.length > 0
          ? state.matters.map(matter => (
            <tr key={matter.id}>
              <td colSpan={2}>
                <a
                  href={`/app/matters/${matter.id}`}
                  className="matter-row"
                >
                  <span className="matter-reference">{matter.external_reference}</span>
                  <span className="matter-title">{matter.title}</span>
                </a>
              </td>
            </tr>
          ))
          : <tr><td colSpan={2}><CollectionMessage state={state} /></td></tr>}
      </tbody>
    </table>
  );
}

function CollectionMessage({ state }: { state: CollectionState }) {
  if (state.status === "loading") {
    return <div className="ledger-empty" role="status">Loading Matters…</div>;
  }
  if (state.status === "failed") {
    return <div className="ledger-empty" role="alert">
      <p>Matters could not be loaded.</p>
      <p>Reload the page to try again.</p>
      <button onClick={() => window.location.reload()}>Reload page</button>
    </div>;
  }
  return <div className="ledger-empty">
    <p>No accepted Matters yet</p>
    <p>Accepted Matters will appear here.</p>
  </div>;
}
