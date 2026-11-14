import { csrfHeaders, request } from "../../../shared/api";

export interface Candidate {
  followUp?: string;
  kind: "email" | "pdf";
  id: string;
  title: string;
}
export interface Hits {
  messages: string[];
  files: { id: string; title: string }[];
  more_pages: boolean;
  stop_reason: string | null;
}
export interface View extends Omit<Hits, "messages"> {
  scope: {
    mailbox: string;
    folder: string;
    label: string;
    first_day: string | null;
    last_day: string | null;
  };
  can_inspect_more: boolean;
  original_query: string;
  revision: number;
  returned_messages: string[];
  pending: string[];
  inspected: string[];
  inspected_titles: Record<string, string>;
  skipped: string[];
  failed: string[];
  requests: number;
  bytes: number;
  suggestions: {
    query: string;
    origin: string;
    passage: string;
    rationale: string;
  }[];
}
export interface EmailMessage {
  title: string;
  text: string;
  sender: string;
  to: string;
  cc: string;
  bcc: string;
  sent_at: string | null;
  gmail_timestamp_ms: number;
}
export interface Preview {
  token: string;
  sources: { id: string; title: string; text: string }[];
}
export interface FollowUp extends Hits {
  revision: number;
  query: string;
}

export async function action<T>(name: string, body: object): Promise<T> {
  const response = await request("/api/matter-proposals/discovery/" + name, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify(body),
  });
  return response.json();
}

export function candidates(
  view: View,
  followups: FollowUp[],
  messageTitle: (id: string, position: number) => string,
) {
  const items = new Map<string, Candidate>();
  const excluded = new Set([...view.skipped, ...view.failed]);
  const original = { messages: view.returned_messages, files: view.files };
  let mailPosition = 0;
  for (const hits of [{ ...original, query: "" }, ...followups]) {
    const origin = hits.query ? { followUp: hits.query } : {};
    for (const id of hits.messages) {
      if (excluded.has(id) || items.has("mail:" + id)) continue;
      mailPosition++;
      items.set("mail:" + id, {
        ...origin,
        kind: "email",
        id,
        title: view.inspected_titles[id] || messageTitle(id, mailPosition),
      });
    }
    for (const file of hits.files) {
      if (items.has("pdf:" + file.id)) continue;
      items.set("pdf:" + file.id, {
        ...origin,
        kind: "pdf",
        id: file.id,
        title: file.title,
      });
    }
  }
  return [...items.values()];
}
