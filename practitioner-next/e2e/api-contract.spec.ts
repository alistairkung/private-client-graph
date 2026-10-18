import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const pdf = readFileSync(
  new URL("../../tests/fixtures/synthetic-proposal.pdf", import.meta.url),
);
const trustPdf = readFileSync(
  new URL("../../tests/fixtures/multiple-role-proposal.pdf", import.meta.url),
);

async function authenticate(
  request: import("@playwright/test").APIRequestContext,
) {
  const response = await request.get("/auth/login?next=/app");
  expect(response.ok()).toBeTruthy();
  const state = await request.storageState();
  const csrf = state.cookies.find(
    (cookie) => cookie.name === "__Host-pcg-csrf",
  )?.value;
  expect(csrf).toBeTruthy();
  return { "x-csrftoken": csrf!, origin: "https://127.0.0.1:5443" };
}

// These tests hit the unchanged backend through the new app's local proxy.
// Only external Google/model dispatches are substituted by the existing dev adapter.
test("existing authentication and CSRF boundaries survive the standalone proxy", async ({
  request,
}) => {
  expect((await request.get("/api/matters")).status()).toBe(401);
  const headers = await authenticate(request);
  expect((await request.get("/api/matters")).status()).toBe(200);
  expect(
    (
      await request.post("/api/matters", {
        data: {},
        headers: { origin: headers.origin },
      })
    ).status(),
  ).toBe(403);
  expect(
    (
      await request.post("/auth/logout", {
        headers: { ...headers, origin: "https://untrusted.invalid" },
      })
    ).status(),
  ).toBe(403);
  expect((await request.post("/auth/logout", { headers })).status()).toBe(204);
  expect((await request.get("/api/matters")).status()).toBe(401);
});

test("multi-source PDF → real canonical proposal → accepted Matter retains exact state", async ({
  request,
}) => {
  const headers = await authenticate(request);
  const form = new FormData();
  form.append("external_reference", `NEXT/API/${crypto.randomUUID()}`);
  form.append("matter_title", "Fictional multi-source integration");
  form.append("synthetic_confirmation", "true");
  form.append(
    "sources",
    JSON.stringify([
      { id: "source_001", title: "Family instruction" },
      { id: "source_002", title: "Trust instruction" },
    ]),
  );
  form.append(
    "pdfs",
    new Blob([pdf], { type: "application/pdf" }),
    "family.pdf",
  );
  form.append(
    "pdfs",
    new Blob([trustPdf], { type: "application/pdf" }),
    "trust.pdf",
  );
  // APIRequestContext accepts repeated parts through an explicit multipart body.
  const boundary = `pcg-next-${crypto.randomUUID()}`;
  const chunks: Buffer[] = [];
  for (const [name, value] of form.entries()) {
    const file = typeof value !== "string";
    chunks.push(
      Buffer.from(
        `--${boundary}\r\nContent-Disposition: form-data; name="${name}"${file ? `; filename="${value.name}"` : ""}\r\n${file ? "Content-Type: application/pdf\r\n" : ""}\r\n`,
      ),
    );
    chunks.push(
      file ? Buffer.from(await value.arrayBuffer()) : Buffer.from(value),
    );
    chunks.push(Buffer.from("\r\n"));
  }
  chunks.push(Buffer.from(`--${boundary}--\r\n`));
  const created = await request.post("/api/matter-proposals", {
    headers: {
      ...headers,
      "content-type": `multipart/form-data; boundary=${boundary}`,
    },
    data: Buffer.concat(chunks),
  });
  expect(created.status(), await created.text()).toBe(201);
  const proposal = await created.json();
  expect(
    proposal.state.sources.map((source: { id: string }) => source.id),
  ).toEqual(["source_001", "source_002"]);
  expect(proposal.authoritative_source).toBeNull();
  expect(
    new Set(
      proposal.state.evidence.map(
        (item: { source_id: string }) => item.source_id,
      ),
    ).size,
  ).toBe(2);
  for (const evidence of proposal.state.evidence) {
    const source = proposal.state.sources.find(
      (item: { id: string }) => item.id === evidence.source_id,
    );
    expect(source.text).toContain(evidence.supporting_text);
  }
  const confirmation = await request.post("/api/matters", {
    headers,
    data: { matter_proposal_id: proposal.id },
  });
  expect(confirmation.status()).toBe(201);
  const location = confirmation.headers().location;
  expect(location).toMatch(/^\/api\/matters\/[^/]+$/);
  const accepted = await (await request.get(location)).json();
  expect(accepted.state).toEqual(proposal.state);
  expect(
    (await request.get(`/api/matter-proposals/${proposal.id}`)).status(),
  ).toBe(404);
});
