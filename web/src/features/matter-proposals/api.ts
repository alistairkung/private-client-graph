import { JsonRequestError, requestJson } from "../../shared/json-request";
import type { MatterProposalDetail, MatterProposalSummary, ProposalInput, ProposalError } from "./types";

export async function createProposal(input: ProposalInput): Promise<MatterProposalDetail> {
  const body = new FormData();
  body.append("external_reference", input.external_reference);
  body.append("matter_title", input.matter_title);
  body.append("source_title", input.source_title);
  body.append("pdf", input.pdf);
  body.append("synthetic_confirmation", String(input.synthetic_confirmation));
  try {
    return await requestJson("/api/matter-proposals", {
      method: "POST", headers: csrfHeaders(), body,
    });
  } catch (error) {
    throw proposalFailure(error, "The intake outcome could not be confirmed. Check the reference and retry to find an existing proposal or Matter before another analysis.");
  }
}

export async function getProposals(): Promise<MatterProposalSummary[]> {
  return requestJson("/api/matter-proposals");
}

export async function getProposal(id: string): Promise<MatterProposalDetail | null> {
  try {
    return await requestJson(`/api/matter-proposals/${encodeURIComponent(id)}`);
  } catch (error) {
    if (error instanceof JsonRequestError && error.status === 404) return null;
    throw error;
  }
}

export async function discardProposal(id: string): Promise<void> {
  try {
    const response = await fetch(`/api/matter-proposals/${encodeURIComponent(id)}`, {
      method: "DELETE", headers: csrfHeaders(),
    });
    if (response.ok) return;
    const body: unknown = await response.json().catch(() => undefined);
    throw new JsonRequestError("http", response.status, body);
  } catch (error) {
    throw proposalFailure(error, "Discard could not be confirmed. Return to Matters to check whether the intake is still awaiting confirmation.");
  }
}

function csrfHeaders(): Record<string, string> {
  const csrf = document.cookie.split("; ").find(value => value.startsWith("__Host-pcg-csrf="))?.split("=")[1] ?? "";
  return { "x-csrftoken": csrf };
}

export class ProposalRequestFailure extends Error {
  constructor(public readonly error: ProposalError) {
    super(error.message);
  }
}

function proposalFailure(failure: unknown, message: string): ProposalRequestFailure {
  if (failure instanceof JsonRequestError) {
    const body = failure.body as { error?: ProposalError } | undefined;
    const error = body?.error;
    if (error && typeof error.code === "string" && typeof error.message === "string" && typeof error.retryable === "boolean") {
      return new ProposalRequestFailure(error);
    }
    if (failure.status === 401 || failure.status === 403) {
      return new ProposalRequestFailure({
        code: "authentication", retryable: false,
        message: failure.status === 401 ? "Your session has expired. Sign in again to continue." : "This request was not allowed. Reload the page to restore your session.",
      });
    }
  }
  return new ProposalRequestFailure({ code: "connection", message, retryable: true, outcome_unknown: true });
}
