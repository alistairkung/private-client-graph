import { useState } from "react";
import { discardProposal, ProposalRequestFailure } from "./api";
import { ProposalFailureNotice } from "./ProposalFailureNotice";
import type { ProposalError } from "./types";

export function DiscardIntake({ id, onNavigate }: { id: string; onNavigate: (path: string) => void }) {
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ProposalError>();
  async function discard() {
    if (pending) return;
    setPending(true);
    setError(undefined);
    try {
      await discardProposal(id);
      onNavigate("/app");
    } catch (failure) {
      if (failure instanceof ProposalRequestFailure) setError(failure.error);
    } finally {
      setPending(false);
    }
  }
  return <div className="discard-intake">
    {confirming ? <section className="discard-confirmation" aria-labelledby="discard-heading">
      <h2 id="discard-heading">Discard this intake?</h2>
      <p>This permanently removes the Matter Proposal, its Authoritative Source, and its proposed graph. It creates no Matter and records no judgment about the relationships.</p>
      <div className="intake-actions">
        <button type="button" className="intake-button secondary" disabled={pending} onClick={() => setConfirming(false)} autoFocus>Keep intake</button>
        <button type="button" className="intake-button destructive" disabled={pending || error?.retryable === false} onClick={discard}>Permanently discard intake</button>
      </div>
      {pending && <p role="status">Discarding intake…</p>}
    </section> : <button type="button" className="intake-button secondary" onClick={() => setConfirming(true)}>Discard intake</button>}
    {error && <ProposalFailureNotice error={error} />}
  </div>;
}
