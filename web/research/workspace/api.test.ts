import { afterEach, expect, it, vi } from "vitest";
import { authorizeRun, controlRun, copyDraft, getRun, saveDraft } from "./api";
afterEach(() => vi.unstubAllGlobals());
it("uses v2 read/copy commands and keeps authorization separate from start with the same invocation identity", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", fetch);
  const signal = new AbortController().signal;
  await getRun("a/b", "r", signal);
  expect(fetch).toHaveBeenLastCalledWith(
    "/api/research/v2/experiments/a%2Fb/runs/r",
    { signal },
  );
  await copyDraft("e", {
    request_id: "copy",
    expected_revision: 2,
    run_id: "r",
  });
  expect(JSON.parse(fetch.mock.calls.at(-1)![1].body)).toEqual({
    request_id: "copy",
    expected_revision: 2,
    run_id: "r",
  });
  const approval = {
    request_id: "invocation",
    plan_digest: "digest",
    approved: true as const,
    task_id: "task",
    expected_task_usage: 1,
    expected_task_cap: 3,
    task_cap: 3,
    continuation: false,
  };
  await authorizeRun("e", "r", approval);
  expect(
    fetch.mock.calls.filter(([url]) => url.endsWith("/start")),
  ).toHaveLength(0);
  await controlRun("e", "r", "start", {
    request_id: approval.request_id,
    plan_digest: approval.plan_digest,
  });
  expect(fetch).toHaveBeenLastCalledWith(
    "/api/research/v2/experiments/e/runs/r/start",
    expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ request_id: "invocation", plan_digest: "digest" }),
    }),
  );
});
it("surfaces backend conflicts without dispatching or retrying", async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: false,
    status: 409,
    json: async () => ({ detail: "Another Run is active" }),
  });
  vi.stubGlobal("fetch", fetch);
  await expect(
    controlRun("e", "r", "start", { request_id: "i", plan_digest: "d" }),
  ).rejects.toThrow("Another Run is active");
  expect(fetch).toHaveBeenCalledTimes(1);
});
