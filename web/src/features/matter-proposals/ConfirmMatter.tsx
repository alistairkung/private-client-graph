import { useState } from "react";
import { confirmProposal, ProposalRequestFailure } from "./api";
import { ProposalFailureNotice } from "./ProposalFailureNotice";
import type { ProposalError } from "./types";

export function ConfirmMatter({ id, onNavigate }: { id: string; onNavigate: (path: string) => void }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ProposalError>();

  async function confirm() {
    if (pending) return;
    setPending(true);
    setError(undefined);
    try {
      onNavigate(await confirmProposal(id));
    } catch (failure) {
      if (failure instanceof ProposalRequestFailure) setError(failure.error);
    } finally {
      setPending(false);
    }
  }

  return <div className="confirm-matter">
    <p>Confirming means the whole proposed graph becomes the professionally accepted current Matter state, together with this Authoritative Source and Matter identity.</p>
    <button
      type="button"
      className="intake-button"
      disabled={pending || error?.retryable === false}
      onClick={confirm}
    >
      Confirm whole graph and create Matter
    </button>
    {pending && <p role="status">Creating Matter…</p>}
    {error && <ProposalFailureNotice error={error} />}
  </div>;
}
