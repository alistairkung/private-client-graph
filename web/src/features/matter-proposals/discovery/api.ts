import { csrfHeaders, request } from "../../../shared/api";

export interface Candidate {
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
  messageTitle: (id: string) => string,
) {
  const items = new Map<string, Candidate>();
  const excluded = new Set([...view.skipped, ...view.failed]);
  const original = { messages: view.returned_messages, files: view.files };
  for (const hits of [original, ...followups]) {
    for (const id of hits.messages) {
      if (!excluded.has(id))
        items.set("mail:" + id, {
          kind: "email",
          id,
          title: view.inspected_titles[id] || messageTitle(id),
        });
    }
    for (const file of hits.files)
      items.set("pdf:" + file.id, {
        kind: "pdf",
        id: file.id,
        title: file.title,
      });
  }
  return [...items.values()];
}
