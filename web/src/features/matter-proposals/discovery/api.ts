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
  original_item_limit: number;
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
export interface PreviewProgress {
  continuation: string;
  completed: number;
  total: number;
}

export function candidateKey(item: Pick<Candidate, "kind" | "id">) {
  return item.kind + ":" + item.id;
}

export interface FollowUp extends Hits {
  revision: number;
  query: string;
}

export async function action<T>(name: string, body: object, signal?: AbortSignal): Promise<T> {
  const response = await request("/api/matter-proposals/discovery/" + name, {
    method: "POST",
    signal,
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify(body),
  });
  return response.json();
}

export type DiscoveredItem =
  | { kind: "email"; id: string; followUp?: string }
  | { kind: "pdf"; id: string; followUp?: string; title: string };

// Apply responses in arrival order. Updating a Map entry preserves its first position.
export function mergeHits(
  previous: DiscoveredItem[],
  hits: Pick<Hits, "messages" | "files">,
  followUp?: string,
): DiscoveredItem[] {
  const items = new Map(previous.map(item => [candidateKey(item), item]));
  for (const id of hits.messages) {
    const email = { kind: "email" as const, id, followUp };
    const key = candidateKey(email);
    if (!items.has(key)) items.set(key, email);
  }
  for (const file of hits.files) {
    const pdf = { kind: "pdf" as const, ...file, followUp };
    const key = candidateKey(pdf);
    const existing = items.get(key);
    items.set(key, existing?.kind === "pdf" ? { ...existing, title: file.title } : pdf);
  }
  return [...items.values()];
}

export function candidates(
  discovered: DiscoveredItem[],
  view: View,
  messageTitle: (position: number) => string,
): Candidate[] {
  const items: Candidate[] = [];
  const excluded = new Set([...view.skipped, ...view.failed]);
  let mailPosition = 0;
  for (const item of discovered) {
    if (item.kind === "email") {
      if (excluded.has(item.id)) continue;
      mailPosition++;
      items.push({ ...item, title: view.inspected_titles[item.id] || messageTitle(mailPosition) });
    } else {
      items.push(item);
    }
  }
  return items;
}
