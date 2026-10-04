import { expect, test, vi } from "vitest";
import { createProposal, discardProposal, getProposal, getProposals } from "./api";

const proposal = {
  id: "proposal-42", external_reference: "Firm/42", matter_title: "Example family",
  authoritative_source: { title: "Attendance note", text: "Fictional source" },
  proposed_graph: { entities: [], relationships: [], evidence: [] },
};

test("creation sends one PDF and synthetic confirmation with the session CSRF token", async () => {
  vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-pcg-csrf=test-csrf");
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(proposal), { status: 201 }));
  const pdf = new File(["%PDF-fixture"], "note.pdf", { type: "application/pdf" });
  await expect(createProposal({ external_reference: "Firm/42", matter_title: "Example family", source_title: "Attendance note", pdf, synthetic_confirmation: true })).resolves.toEqual(proposal);
  expect(fetcher).toHaveBeenCalledOnce();
  const [url, options] = fetcher.mock.calls[0];
  expect(url).toBe("/api/matter-proposals");
  expect(options?.method).toBe("POST");
  expect(options?.headers).toEqual({ "x-csrftoken": "test-csrf" });
  const form = options?.body as FormData;
  expect(Array.from(form.keys())).toEqual(["external_reference", "matter_title", "source_title", "pdf", "synthetic_confirmation"]);
  expect(form.get("pdf")).toBe(pdf);
  expect(form.get("synthetic_confirmation")).toBe("true");
});

test("creation preserves typed recovery and never exposes proxy diagnostics", async () => {
  const input = { external_reference: "Firm/42", matter_title: "Example family", source_title: "Note", pdf: new File(["pdf"], "note.pdf"), synthetic_confirmation: true };
  const error = { code: "duplicate_reference", message: "This reference already exists.", retryable: false, existing_resource: { resource_kind: "matter_proposal", resource_id: "proposal-42", location: "/api/matter-proposals/proposal-42" } };
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response(JSON.stringify({ error }), { status: 409 }))
    .mockResolvedValueOnce(new Response("<html>secret proxy diagnostics</html>", { status: 502 }))
    .mockRejectedValueOnce(new TypeError("Failed to fetch"));
  await expect(createProposal(input)).rejects.toMatchObject({ error });
  for (let attempt = 0; attempt < 2; attempt++) {
    await expect(createProposal(input)).rejects.toMatchObject({ error: { outcome_unknown: true, retryable: true, message: expect.stringContaining("could not be confirmed") } });
  }
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test("proposal discovery uses separate persisted resources and a missing detail stays missing", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response(JSON.stringify([{ id: proposal.id, external_reference: proposal.external_reference, matter_title: proposal.matter_title }])))
    .mockResolvedValueOnce(new Response(JSON.stringify(proposal)))
    .mockResolvedValueOnce(new Response("{}", { status: 404 }));
  expect(await getProposals()).toEqual([{ id: "proposal-42", external_reference: "Firm/42", matter_title: "Example family" }]);
  expect(await getProposal("proposal/42")).toEqual(proposal);
  expect(await getProposal("missing")).toBeNull();
  expect(fetcher.mock.calls.map(call => call[0])).toEqual(["/api/matter-proposals", "/api/matter-proposals/proposal%2F42", "/api/matter-proposals/missing"]);
});

test("discard accepts an empty success response and treats a lost response as ambiguous", async () => {
  vi.spyOn(document, "cookie", "get").mockReturnValue("__Host-pcg-csrf=discard-csrf");
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
    .mockRejectedValueOnce(new TypeError("Network disconnected"));
  await expect(discardProposal("proposal/42")).resolves.toBeUndefined();
  expect(fetcher.mock.calls[0]).toEqual(["/api/matter-proposals/proposal%2F42", { method: "DELETE", headers: { "x-csrftoken": "discard-csrf" } }]);
  await expect(discardProposal("proposal/42")).rejects.toMatchObject({ error: { outcome_unknown: true, message: expect.stringContaining("could not be confirmed") } });
});
