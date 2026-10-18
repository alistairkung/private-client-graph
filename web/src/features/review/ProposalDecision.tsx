import { useAccess } from "../../shared/access";
import { useState } from "react";
import { navigate, useNavigationLock } from "../../app/navigation";
import type { CanonicalState, ReviewRecord } from "../../shared/contracts";
import { useLocale } from "../../shared/locale";
import {
  confirmProposal,
  discardProposal,
  RequestFailure,
} from "../../shared/api";
import { Dialog } from "../../shared/Dialog";
import { ErrorNotice } from "../../shared/Feedback";

export function ProposalDecision({
  decision,
  record,
  state,
  error,
  blocked,
  onError,
  onClose,
}: {
  decision: "confirm" | "discard";
  record: ReviewRecord;
  state: CanonicalState;
  error?: unknown;
  blocked: boolean;
  onError: (error: unknown) => void;
  onClose: () => void;
}) {
  const { access } = useAccess();
  const { t } = useLocale();
  const [busy, setBusy] = useState(false);
  useNavigationLock(busy);
  const confirm = decision === "confirm";
  async function submit() {
    if (busy || blocked || !access?.can_write) return;
    setBusy(true);
    onError(undefined);
    try {
      if (confirm) navigate(await confirmProposal(record.id));
      else {
        await discardProposal(record.id);
        navigate("/app");
      }
    } catch (failure) {
      onError(failure);
      setBusy(false);
    }
  }
  return (
    <Dialog
      title={t(
        confirm
          ? "Confirm the complete proposal?"
          : "Discard the complete proposal?",
      )}
      onClose={onClose}
      busy={busy}
    >
      <p>
        {t(
          confirm
            ? "This creates a Matter with the entire proposed graph as its professionally accepted current state."
            : "This removes the saved proposal and its sources. It will not create a Matter.",
        )}
      </p>
      <div className="decision-record">
        <strong>{record.external_reference}</strong>
        <span>{record.matter_title}</span>
        <span>
          {t("{sources} sources · {relationships} relationships", {
            sources: state.sources.length,
            relationships: state.relationships.length,
          })}
        </span>
      </div>
      {error !== undefined && <ErrorNotice error={error} />}
      <div className="dialog-actions">
        <button
          className={"button " + (confirm ? "primary" : "destructive")}
          disabled={busy || blocked || !access?.can_write}
          onClick={submit}
        >
          {t(
            busy
              ? confirm
                ? "Confirming…"
                : "Discarding…"
              : confirm
                ? "Confirm and create Matter"
                : "Discard entire proposal",
          )}
        </button>
        <button className="button" disabled={busy} onClick={onClose}>
          {t("Keep reviewing")}
        </button>
      </div>
    </Dialog>
  );
}

export function decisionIsBlocked(error: unknown): boolean {
  return (
    error instanceof RequestFailure &&
    Boolean(
      error.detail?.outcome_unknown ||
        error.detail?.retryable === false ||
        error.status === 401 ||
        error.status === 403,
    )
  );
}
