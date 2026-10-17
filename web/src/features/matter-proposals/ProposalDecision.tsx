import { useLocale } from "../../shared/locale";
import { useEffect, useRef, useState } from "react";
import { confirmProposal, discardProposal, ProposalRequestFailure } from "./api";
import { ProposalFailureNotice } from "./ProposalFailureNotice";
import { rememberMatterCreation } from "../matters/creation-notice";
import type { MatterProposalDetail, ProposalError } from "./types";

export function ProposalDecision({ proposal, onNavigate }: {
  proposal: MatterProposalDetail;
  onNavigate: (path: string) => void;
}) {
  const { t } = useLocale();
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
  return <section className="proposal-decision" aria-label={t("Matter Proposal decision")} aria-busy={!!pending}>
    {discarding ? <section className="discard-confirmation" aria-labelledby="discard-heading">
      <h2 id="discard-heading">{t("Discard this intake?")}</h2>
      <p className="discard-identity">{proposal.matter_title} · {proposal.external_reference}</p>
      <p>{t("This permanently removes the saved proposal, all its source text and its proposed graph. No Matter will be created.")}</p>
      <p>{t("Discarding records no judgment about the relationships.")}</p>
      <div className="intake-actions">
        <button ref={keepButton} className="intake-button secondary" disabled={!!pending} onClick={() => {
          returnFocus.current = true;
          setDiscarding(false);
          // An uncertain terminal outcome must be resolved through the collections.
          if (!error?.outcome_unknown) setError(undefined);
        }}>{t("Keep intake")}</button>
        <button className="intake-button destructive" disabled={blocked} onClick={() => void decide("discard")}>{t("Permanently discard intake")}</button>
      </div>
    </section> : <>
      <h2>{t("Accept this proposal?")}</h2>
      <p>{t("Confirming means the whole proposed graph becomes the professionally accepted current Matter state, together with all supplied Sources and Matter identity.")}</p>
      <div className="decision-actions">
        <button className="intake-button" disabled={blocked} onClick={() => void decide("confirm")}>{t("Confirm and create Matter")}</button>
        <a className="decision-return" href="/app">{t("Back to Matters")}</a>
        <button ref={discardButton} className="discard-trigger" disabled={blocked} onClick={() => {
          setError(undefined);
          setDiscarding(true);
        }}>{t("Discard intake")}</button>
      </div>
    </>}
    {pending && <p role="status">{pending === "confirm" ? t("Creating Matter…") : t("Discarding intake…")}</p>}
    {error && <ProposalFailureNotice error={error} />}
  </section>;
}
