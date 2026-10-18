import type {
  IntakeInput,
  MatterSummary,
  ProposalSummary,
  ReviewRecord,
  ServiceError,
} from "./contracts";
export class RequestFailure extends Error {
  constructor(
    public status: number,
    public detail?: ServiceError,
  ) {
    super(detail?.message ?? "Request failed");
  }
}
export function csrfHeaders(): Record<string, string> {
  const token =
    document.cookie
      .split("; ")
      .find((item) => item.startsWith("__Host-pcg-csrf="))
      ?.slice("__Host-pcg-csrf=".length) ?? "";
  return { "x-csrftoken": token };
}
export async function request(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(path, { credentials: "same-origin", ...init });
  } catch {
    throw new RequestFailure(0, {
      code: "connection",
      message: "",
      retryable: true,
      outcome_unknown: !!init?.method,
    });
  }
  if (!response.ok) {
    if (init?.method && (response.status === 401 || response.status === 403)) {
      window.dispatchEvent(new Event("pcg:access-denied"));
    }
    const body = (await response.json().catch(() => undefined)) as
      | { error?: ServiceError }
      | undefined;
    const detail = body?.error;
    const valid =
      detail &&
      typeof detail.code === "string" &&
      typeof detail.message === "string" &&
      typeof detail.retryable === "boolean";
    const fallback =
      init?.method && response.status !== 401 && response.status !== 403
        ? {
            code: "outcome_unknown",
            message: "",
            retryable: false,
            outcome_unknown: true,
          }
        : undefined;
    throw new RequestFailure(response.status, valid ? detail : fallback);
  }
  return response;
}
async function json<T>(path: string): Promise<T> {
  return (await request(path)).json() as Promise<T>;
}
export const getMatters = () => json<MatterSummary[]>("/api/matters");
export const getProposals = () =>
  json<ProposalSummary[]>("/api/matter-proposals");
export const getReview = (kind: "matters" | "matter-proposals", id: string) =>
  json<ReviewRecord>("/api/" + kind + "/" + encodeURIComponent(id));
export async function createProposal(
  input: IntakeInput,
): Promise<ReviewRecord> {
  const body = new FormData();
  body.append("external_reference", input.external_reference);
  body.append("matter_title", input.matter_title);
  body.append("synthetic_confirmation", String(input.synthetic_confirmation));
  if (input.sources.length === 1) {
    body.append("source_title", input.sources[0].title);
    body.append("pdf", input.sources[0].pdf);
  } else {
    body.append(
      "sources",
      JSON.stringify(input.sources.map(({ id, title }) => ({ id, title }))),
    );
    input.sources.forEach((source) => body.append("pdfs", source.pdf));
  }
  const response = await request("/api/matter-proposals", {
    method: "POST",
    headers: csrfHeaders(),
    body,
  });
  try {
    const record = (await response.json()) as ReviewRecord;
    if (!record || typeof record.id !== "string")
      throw new Error("Invalid proposal response");
    return record;
  } catch {
    throw new RequestFailure(response.status, {
      code: "outcome_unknown",
      message: "",
      retryable: false,
      outcome_unknown: true,
    });
  }
}
export async function confirmProposal(id: string): Promise<string> {
  const response = await request("/api/matters", {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ matter_proposal_id: id }),
  });
  const location = response.headers.get("Location");
  if (
    response.status !== 201 ||
    !location ||
    !/^\/api\/matters\/[^/?#]+$/.test(location)
  ) {
    throw new RequestFailure(0, {
      code: "confirmation_outcome_unknown",
      message: "",
      retryable: false,
      outcome_unknown: true,
    });
  }
  return location.replace(/^\/api\//, "/app/");
}
export async function discardProposal(id: string): Promise<void> {
  await request("/api/matter-proposals/" + encodeURIComponent(id), {
    method: "DELETE",
    headers: csrfHeaders(),
  });
}
export async function signOut(): Promise<void> {
  await request("/auth/logout", { method: "POST", headers: csrfHeaders() });
}
export function existingPath(error: ServiceError): string | undefined {
  const resource = error.existing_resource;
  if (
    !resource ||
    !["matter", "matter_proposal"].includes(resource.resource_kind) ||
    typeof resource.resource_id !== "string"
  )
    return;
  return (
    "/app/" +
    (resource.resource_kind === "matter" ? "matters" : "matter-proposals") +
    "/" +
    encodeURIComponent(resource.resource_id)
  );
}
