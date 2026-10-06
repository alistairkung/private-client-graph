import { useEffect, useState } from "react";
import { getProposals } from "./api";
import type { MatterProposalSummary } from "./types";

type CollectionState =
  | { status: "loading" | "failed" }
  | { status: "ready"; proposals: MatterProposalSummary[] };

export function ProposalCollection() {
  const [state, setState] = useState<CollectionState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    getProposals().then(
      proposals => { if (active) setState({ status: "ready", proposals }); },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, []);

  return <section className="proposal-collection" aria-labelledby="awaiting-confirmation">
    <h2 id="awaiting-confirmation">Awaiting confirmation</h2>
    <p>These saved proposals need your review before a Matter is created.</p>
    <table className="matter-register" aria-label="Matter Proposals awaiting confirmation">
      <thead><tr><th scope="col">Matter reference</th><th scope="col">Matter</th></tr></thead>
      <tbody>
        {state.status === "ready" && state.proposals.length > 0 ? state.proposals.map(proposal => (
          <tr key={proposal.id}><td colSpan={2}>
            <a href={`/app/matter-proposals/${encodeURIComponent(proposal.id)}`} className="matter-row">
              <span className="matter-reference">{proposal.external_reference}</span>
              <span className="matter-title">{proposal.matter_title}</span>
            </a>
          </td></tr>
        )) : <tr><td colSpan={2}>
          {state.status === "loading" ? <div className="ledger-empty" role="status">Loading Matter Proposals…</div> :
            state.status === "failed" ? <div className="ledger-empty" role="alert"><p>Matter Proposals could not be loaded.</p><p>Reload the page to try again.</p><button onClick={() => window.location.reload()}>Reload page</button></div> :
              <div className="ledger-empty"><p>No Matter Proposals awaiting confirmation</p><p>Create a Matter to upload and analyse a synthetic source.</p></div>}
        </td></tr>}
      </tbody>
    </table>
  </section>;
}
