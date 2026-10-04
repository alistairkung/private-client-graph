import { expect, test, vi } from "vitest";
import { requestJson } from "./json-request";

test("returns parsed JSON from one request with unchanged request options", async () => {
  const options = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: '{"mode":"live"}',
  };
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ result: "ok" })),
  );

  await expect(
    requestJson<{ result: string }>("/resource", options),
  ).resolves.toEqual({ result: "ok" });
  expect(fetcher).toHaveBeenCalledExactlyOnceWith("/resource", options);
});

test("retains the status and parsed body from an unsuccessful response", async () => {
  const body = { error: { message: "Unavailable" } };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), { status: 503 }),
  );

  await expect(requestJson("/resource")).rejects.toEqual(
    expect.objectContaining({
      kind: "http",
      status: 503,
      body,
    }),
  );
});

test("identifies a network failure without retrying", async () => {
  const fetcher = vi
    .spyOn(globalThis, "fetch")
    .mockRejectedValue(new TypeError("Failed to fetch"));

  await expect(requestJson("/resource")).rejects.toEqual(
    expect.objectContaining({ kind: "network" }),
  );
  expect(fetcher).toHaveBeenCalledOnce();
});

test("identifies invalid JSON and retains its response status", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("<html>proxy diagnostics</html>", { status: 502 }),
  );

  await expect(requestJson("/resource")).rejects.toEqual(
    expect.objectContaining({ kind: "invalid-json", status: 502 }),
  );
});
