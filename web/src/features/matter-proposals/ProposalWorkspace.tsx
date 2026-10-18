import { useLocale } from "../../shared/locale";
import { useEffect, useLayoutEffect, useState } from "react";
import { ReviewWorkspace } from "../review/ReviewWorkspace";
import { SourceAwareReviewWorkspace } from "../review/SourceAwareReviewWorkspace";
import { getProposal } from "./api";
import { ProposalDecision } from "./ProposalDecision";
import type { MatterProposalDetail } from "./types";

type ProposalState =
  | { status: "loading" | "missing" | "failed" }
  | { status: "ready"; proposal: MatterProposalDetail };

export function ProposalWorkspace({ id, onNavigate, canWrite = false }: { id: string; onNavigate: (path: string) => void; canWrite?: boolean }) {
  const { t } = useLocale();
  const [state, setState] = useState<ProposalState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    getProposal(id).then(
      proposal => {
        if (!active) return;
        setState(proposal ? { status: "ready", proposal } : { status: "missing" });
      },
      () => { if (active) setState({ status: "failed" }); },
    );
    return () => { active = false; };
  }, [id]);

  useLayoutEffect(() => {
    document.title = `${state.status === "ready" ? state.proposal.matter_title : t("Matter Proposal not found")} · Private Client Graph`;
  }, [state, t]);

  return <>
    <a className="matter-back" href="/app">{t("Back to Matters")}</a>
    {state.status === "ready" ? <>
      <header className="matter-context">
        <h1>{state.proposal.matter_title}</h1>
        <p>{t("Matter reference: {reference}", { reference: state.proposal.external_reference })}</p>
        <p className="proposal-explanation">{t("Awaiting confirmation. These relationships are proposed; no Matter has been created.")}</p>
        <p className="proposal-saved">{t("Your proposal is saved. You can return to it from Matters.")}</p>
      </header>
      {state.proposal.state ? <SourceAwareReviewWorkspace key={id} state={state.proposal.state}
        graphTitle={t("Proposed relationships")} emptyGraphTitle={t("No supported relationships proposed")} practitioner />
        : state.proposal.authoritative_source ? <ReviewWorkspace
        source={state.proposal.authoritative_source.text}
        sourceTitle={state.proposal.authoritative_source.title}
        graph={state.proposal.proposed_graph}
        graphTitle={t("Proposed relationships")}
        emptyGraphTitle={t("No supported relationships proposed")}
        practitioner
      /> : <p role="alert">{t("The complete Source state is unavailable. Reload to try again.")}</p>}
      {canWrite && <ProposalDecision proposal={state.proposal} onNavigate={onNavigate} />}
    </> : state.status === "loading" ? <p role="status">{t("Loading Matter Proposal…")}</p> : <div role="alert">
      <h1>{state.status === "missing" ? t("Matter Proposal not found") : t("Matter Proposal could not be loaded.")}</h1>
      <p>{state.status === "missing" ? t("This intake is no longer available. Return to Matters to view the current collections.") : t("Reload the page to try again.")}</p>
    </div>}
  </>;
}
