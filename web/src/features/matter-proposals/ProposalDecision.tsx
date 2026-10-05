import { useEffect, useRef, useState } from "react";
import { confirmProposal, discardProposal, ProposalRequestFailure } from "./api";
import { ProposalFailureNotice } from "./ProposalFailureNotice";
import { rememberMatterCreation } from "../matters/creation-notice";
import type { MatterProposalDetail, ProposalError } from "./types";

export function ProposalDecision({ proposal, onNavigate }: {
  proposal: MatterProposalDetail;
  onNavigate: (path: string) => void;
}) {
  const [discarding, setDiscarding] = useState(false);
  const [pending, setPending] = useState<"confirm" | "discard">();
  const [error, setError] = useState<ProposalError>();
  const discardButton = useRef<HTMLButtonElement>(null);
  const keepButton = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef(false);
  useEffect(() => {
    if (discarding) keepButton.current?.focus();
    else if (returnFocus.current) {
      discardButton.current?.focus();
      returnFocus.current = false;
    }
  }, [discarding]);

  async function decide(action: "confirm" | "discard") {
    if (pending || error?.retryable === false || error?.outcome_unknown) return;
    setPending(action);
    setError(undefined);
    try {
      if (action === "confirm") {
        const path = await confirmProposal(proposal.id);
        rememberMatterCreation(path);
        onNavigate(path);
      } else {
        await discardProposal(proposal.id);
        onNavigate("/app");
      }
    } catch (failure) {
      if (failure instanceof ProposalRequestFailure) setError(failure.error);
    } finally {
      setPending(undefined);
    }
  }

  const blocked = !!pending || error?.retryable === false || !!error?.outcome_unknown;
  return <section className="proposal-decision" aria-label="Matter Proposal decision" aria-busy={!!pending}>
    {discarding ? <section className="discard-confirmation" aria-labelledby="discard-heading">
      <h2 id="discard-heading">Discard this intake?</h2>
      <p className="discard-identity">{proposal.matter_title} · {proposal.external_reference}</p>
      <p>This permanently removes the saved proposal, its source text and its proposed graph. No Matter will be created.</p>
      <p>Discarding records no judgment about the relationships.</p>
      <div className="intake-actions">
        <button ref={keepButton} className="intake-button secondary" disabled={!!pending} onClick={() => {
          returnFocus.current = true;
          setDiscarding(false);
          // An uncertain terminal outcome must be resolved through the collections.
          if (!error?.outcome_unknown) setError(undefined);
        }}>Keep intake</button>
        <button className="intake-button destructive" disabled={blocked} onClick={() => void decide("discard")}>Permanently discard intake</button>
      </div>
    </section> : <>
      <h2>Accept this proposal?</h2>
      <p>Confirming means the whole proposed graph becomes the professionally accepted current Matter state, together with this Authoritative Source and Matter identity.</p>
      <div className="decision-actions">
        <button className="intake-button" disabled={blocked} onClick={() => void decide("confirm")}>Confirm and create Matter</button>
        <a className="decision-return" href="/app">Back to Matters</a>
        <button ref={discardButton} className="discard-trigger" disabled={blocked} onClick={() => {
          setError(undefined);
          setDiscarding(true);
        }}>Discard intake</button>
      </div>
    </>}
    {pending && <p role="status">{pending === "confirm" ? "Creating Matter…" : "Discarding intake…"}</p>}
    {error && <ProposalFailureNotice error={error} />}
  </section>;
}
