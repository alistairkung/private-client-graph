import { afterEach, expect, it, vi } from "vitest";
import { control, preview } from "./api";
import type { Proposal } from "../shared/contracts";

afterEach(() => vi.unstubAllGlobals());
it("sends a single plan-bound command and surfaces backend rejection without retry", async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: false,
    status: 409,
    json: async () => ({ detail: "Task ledger relocation is unsafe" }),
  });
  vi.stubGlobal("fetch", fetch);
  const command = { request_id: "stable-request", plan_digest: "a".repeat(64) };
  await expect(control("frozen-id", "continue", command)).rejects.toThrow(
    "Task ledger relocation is unsafe",
  );
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith(
    "/api/research/v1/plans/frozen-id/continue",
    expect.objectContaining({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    }),
  );
});
it("preserves the server preview and propagates abort for stale configuration", async () => {
  const response = { matrix_call_maximum: 9, task_paid_remaining: 0 };
  const fetch = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => response });
  vi.stubGlobal("fetch", fetch);
  const signal = new AbortController().signal;
  const proposal: Proposal = {
    input_ids: ["case_03_fixture"],
    input_mode: "fresh",
    execution_mode: "recorded",
    resolver: "generative",
    extraction_samples: 3,
    resolver_repetitions: 2,
    invocation_cap: 2,
    model: "deepseek-flash",
    timeout_seconds: 90,
    temperature: null,
    task_call_cap: 0,
  };
  expect(await preview(proposal, signal)).toEqual(response);
  expect(fetch).toHaveBeenCalledWith(
    "/api/research/v1/preview",
    expect.objectContaining({ signal, body: JSON.stringify(proposal) }),
  );
});

it("distinguishes an absent execution composition from an unavailable capability read", async () => {
  const { capabilities } = await import("./api");
  const fetch = vi
    .fn()
    .mockResolvedValueOnce({ status: 404 })
    .mockResolvedValueOnce({ status: 503, ok: false });
  vi.stubGlobal("fetch", fetch);
  expect(await capabilities()).toBeNull();
  await expect(capabilities()).rejects.toThrow(
    "Execution capabilities unavailable",
  );
});
