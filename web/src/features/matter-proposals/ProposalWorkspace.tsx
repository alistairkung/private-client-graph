import { useEffect, useState } from "react";
import { ReviewWorkspace } from "../review/ReviewWorkspace";
import { getProposal } from "./api";
import { ProposalDecision } from "./ProposalDecision";
import type { MatterProposalDetail } from "./types";

type ProposalState =
  | { status: "loading" | "missing" | "failed" }
  | { status: "ready"; proposal: MatterProposalDetail };

export function ProposalWorkspace({ id, onNavigate }: { id: string; onNavigate: (path: string) => void }) {
  const [state, setState] = useState<ProposalState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    getProposal(id).then(
      proposal => {
        if (!active) return;
        setState(proposal ? { status: "ready", proposal } : { status: "missing" });
        document.title = `${proposal?.matter_title ?? "Matter Proposal not found"} · Private Client Graph`;
      },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, [id]);

  return <>
    <a className="matter-back" href="/app">Back to Matters</a>
    {state.status === "ready" ? <>
      <header className="matter-context">
        <h1>{state.proposal.matter_title}</h1>
        <p>Matter reference: {state.proposal.external_reference}</p>
        <p className="proposal-explanation">Awaiting confirmation. These relationships are proposed; no Matter has been created.</p>
        <p className="proposal-saved">Your proposal is saved. You can return to it from Matters.</p>
      </header>
      <ReviewWorkspace
        source={state.proposal.authoritative_source.text}
        sourceTitle={state.proposal.authoritative_source.title}
        graph={state.proposal.proposed_graph}
        graphTitle="Proposed relationships"
        emptyGraphTitle="No supported relationships proposed"
        practitioner
      />
      <ProposalDecision proposal={state.proposal} onNavigate={onNavigate} />
    </> : state.status === "loading" ? <p role="status">Loading Matter Proposal…</p> : <div role="alert">
      <h1>{state.status === "missing" ? "Matter Proposal not found" : "Matter Proposal could not be loaded."}</h1>
      <p>{state.status === "missing" ? "This intake is no longer available. Return to Matters to view the current collections." : "Reload the page to try again."}</p>
    </div>}
  </>;
}
