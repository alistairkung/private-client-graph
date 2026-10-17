import type { ProposalError } from "./types";

// Only repository-owned messages are presented; server diagnostics never enter the UI.
const messages: Record<string, string> = {
  "confirmation_outcome_unknown": "The confirmation outcome is unknown. Check the Matter Ledger to see whether the Matter was created before taking further action.",
  "confirmation_failed": "The Matter could not be created. The Matter Proposal remains available. You may retry confirmation.",
  "invalid_proposal": "The Matter Proposal could not be confirmed because its stored state is invalid. It remains available for review or discard.",
  "provider_authorization_unavailable": "Shared provider authorization is unavailable. No analysis was started.",
  "provider_allowance_exhausted": "The approved shared provider allowance is exhausted. No analysis was started.",
  "provider_outcome_unknown": "The provider outcome could not be retained. Contact the operator before retrying.",
  "duplicate_reference": "This external Matter reference already exists.",
  "persistence_failed": "No Matter Proposal was saved. You may retry the full analysis.",
  "invalid_graph": "No valid proposal was produced. The proposed relationships or Evidence failed validation. You may try a fresh analysis.",
  "outcome_unknown": "The outcome is unknown. Retry to check the external reference before any new analysis.",
  "analysis_unavailable": "Proposal analysis is unavailable. Contact the deployment operator.",
  "allowance_exhausted": "The analysis allowance is exhausted.",
  "reference_unavailable": "The external reference could not be checked. No analysis was started. Retry when available.",
  "invalid_extraction": "No valid proposal was produced. You may try a fresh analysis.",
  "allowance_unavailable": "The analysis allowance could not be checked. No analysis was started.",
  "pdf_too_large": "Select PDFs totalling no more than 10 MiB.",
  "invalid_pdf": "Select a valid text-layer PDF.",
  "encrypted_pdf": "Select an unencrypted text-layer PDF.",
  "pdf_too_many_pages": "Select a PDF containing no more than 50 pages.",
  "pdf_not_extractable": "Select a PDF containing extractable text. OCR is unsupported.",
  "pdf_acquisition_failed": "PDF text acquisition is temporarily unavailable. Retry with the same PDF.",
  "source_too_long": "Select PDFs with at most 100,000 extracted characters combined.",
  "invalid_sources": "Supply between one and five Sources with distinct identifiers.",
  "proposal_not_found": "Matter Proposal not found.",
  "invalid_metadata": "Enter a valid Matter reference and a distinct identifier and title for each Source.",
  "proposals_unavailable": "Matter Proposals could not be loaded.",
  "proposal_unavailable": "Matter Proposal could not be loaded.",
  "discard_unavailable": "The intake could not be discarded. Reload to try again.",
  "invalid_form": "Supply each required text field once and one PDF per Source.",
  "synthetic_confirmation_required": "Confirm that the material is synthetic or fictional.",
  "connection": "The intake outcome could not be confirmed. Check the reference and retry to find an existing proposal or Matter before another analysis.",
  "provider_failed": "Analysis could not finish. No proposal was saved.",
  "provider_transient": "Analysis could not finish. No proposal was saved.",
  "provider_configuration": "Analysis is unavailable.",
  "quota_exhausted": "The analysis allowance is exhausted.",
  "rollback": "No Matter was saved. Try again.",
  "authentication": "Your session has expired. Sign in again to continue.",
  "discard_failed": "The intake could not be discarded. It remains available. You may retry discard."
};

export function proposalFailureMessage(error: ProposalError): string {
  if (error.code === "authentication" && error.message === "This request was not allowed. Reload the page to restore your session.") {
    return "This request was not allowed. Reload the page to restore your session.";
  }
  if (error.code === "connection") {
    if (error.message.startsWith("Discard could not be confirmed.")) {
      return "Discard could not be confirmed. Return to Matters to check whether the intake is still awaiting confirmation.";
    }
    if (error.message.startsWith("Confirmation could not be confirmed.")) {
      return "Confirmation could not be confirmed. Check the Matter Ledger to determine whether the Matter was created.";
    }
  }
  if (error.code === "discard_failed" && error.outcome_unknown) {
    return "The discard outcome is unknown. Reload to check whether the intake remains.";
  }
  return messages[error.code] ?? "The request could not be completed. Return to Matters and check the current state before retrying.";
}
