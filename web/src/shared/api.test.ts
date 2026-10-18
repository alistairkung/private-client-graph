import { afterEach, describe, expect, it, vi } from "vitest";
import {
  confirmProposal,
  createProposal,
  existingPath,
  RequestFailure,
  request,
  signOut,
} from "./api";
import type { IntakeInput } from "./contracts";

const input: IntakeInput = {
  external_reference: "FICTIONAL-1",
  matter_title: "Synthetic family",
  synthetic_confirmation: true,
  sources: [
    {
      id: "stable-one",
      title: "First note",
      pdf: new File(["synthetic"], "note.pdf", { type: "application/pdf" }),
    },
  ],
};
afterEach(() => vi.unstubAllGlobals());
describe("unchanged practitioner request contracts", () => {
  it("sends the single PDF contract with same-origin cookies and CSRF", async () => {
    document.cookie = "__Host-pcg-csrf=csrf-value; path=/; secure";
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ id: "proposal-1" }), { status: 201 }),
      );
    vi.stubGlobal("fetch", fetcher);
    await createProposal(input);
    const [url, options] = fetcher.mock.calls[0];
    expect(url).toBe("/api/matter-proposals");
    expect(options.credentials).toBe("same-origin");
    expect(options.headers).toEqual({ "x-csrftoken": expect.any(String) });
    const form = options.body as FormData;
    expect(form.get("external_reference")).toBe("FICTIONAL-1");
    expect(form.get("synthetic_confirmation")).toBe("true");
    expect(form.get("source_title")).toBe("First note");
    expect(form.get("pdf")).toBeInstanceOf(File);
    expect(form.has("sources")).toBe(false);
  });
  it("preserves distinct stable IDs and file order for multiple sources", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ id: "p" }), { status: 201 }),
      );
    vi.stubGlobal("fetch", fetcher);
    const second = {
      ...input.sources[0],
      id: "stable-two",
      title: "First note",
    };
    await createProposal({ ...input, sources: [input.sources[0], second] });
    const form = fetcher.mock.calls[0][1].body as FormData;
    expect(JSON.parse(String(form.get("sources")))).toEqual([
      { id: "stable-one", title: "First note" },
      { id: "stable-two", title: "First note" },
    ]);
    expect(form.getAll("pdfs")).toHaveLength(2);
    expect(form.has("pdf")).toBe(false);
  });
  it("maps only an explicit confirmation 201 Location to the app", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(null, {
          status: 201,
          headers: { Location: "/api/matters/matter-1" },
        }),
      ),
    );
    await expect(confirmProposal("proposal-1")).resolves.toBe(
      "/app/matters/matter-1",
    );
  });
  it.each([
    new Response("broken JSON", { status: 201 }),
    new Response(JSON.stringify({}), { status: 201 }),
    new Response("proxy unavailable", { status: 502 }),
  ])(
    "preserves unknown creation outcomes without suggesting blind resubmission",
    async (response) => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
      await expect(createProposal(input)).rejects.toMatchObject({
        detail: { outcome_unknown: true, retryable: false },
      });
    },
  );
  it("does not trust malformed error retryability", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: { code: "provider_failed", retryable: "yes", message: 42 },
          }),
          { status: 500 },
        ),
      ),
    );
    await expect(createProposal(input)).rejects.toMatchObject({
      detail: { outcome_unknown: true },
    });
  });
  it("preserves structured duplicate links with encoded IDs and ignores returned locations", async () => {
    const detail = {
      code: "duplicate_reference",
      message: "private diagnostic",
      retryable: false,
      existing_resource: {
        resource_kind: "matter" as const,
        resource_id: "matter/1",
        location: "https://unsafe.invalid",
      },
    };
    expect(existingPath(detail)).toBe("/app/matters/matter%2F1");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ error: detail }), { status: 409 }),
        ),
    );
    await expect(createProposal(input)).rejects.toMatchObject({ detail });
  });
  it("keeps authentication errors available to the page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 401 })),
    );
    await expect(request("/api/matters")).rejects.toBeInstanceOf(
      RequestFailure,
    );
    await expect(request("/api/matters")).rejects.toMatchObject({
      status: 401,
    });
  });
  it("rejects unexpected confirmation locations as unknown", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(null, {
          status: 201,
          headers: { Location: "https://invalid.example/api/matters/a" },
        }),
      ),
    );
    await expect(confirmProposal("p")).rejects.toMatchObject({
      detail: { outcome_unknown: true },
    });
  });
  it("signs out through a protected POST", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetcher);
    await signOut();
    expect(fetcher).toHaveBeenCalledWith(
      "/auth/logout",
      expect.objectContaining({
        method: "POST",
        headers: { "x-csrftoken": expect.any(String) },
        credentials: "same-origin",
      }),
    );
  });
});
