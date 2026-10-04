import { expect, test, vi } from "vitest";
import { analyseCase, getCase, RequestFailure } from "./api";

test("analysis sends only the explicit mode and never retries or falls back", async () => {
  const fetcher = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { stage: "provider", message: "Unavailable", retryable: true },
        }),
        { status: 502 },
      ),
    );
  await expect(analyseCase("live")).rejects.toMatchObject({
    error: { stage: "provider", retryable: true },
  });
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher).toHaveBeenCalledWith(
    "/api/showcase/case-01/analysis",
    expect.objectContaining({ method: "POST", body: '{"mode":"live"}' }),
  );
});

test("case requests propagate transport failures without exposing raw responses", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("<html>proxy diagnostics</html>", { status: 502 }),
  );
  await expect(getCase()).rejects.toBeInstanceOf(RequestFailure);
  await expect(getCase()).rejects.toThrow("could not be reached");
});

test("source loads from the showcase contract", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ title: "Case 01" })),
  );
  await getCase();
  expect(fetcher).toHaveBeenCalledWith("/api/showcase/case-01", undefined);
});
