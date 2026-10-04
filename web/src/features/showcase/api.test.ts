import { expect, test, vi } from "vitest";
import { analyseCase, getCase, RequestFailure } from "./api";

test.each([429, 503])(
  "analysis preserves the complete structured error from HTTP %s without retrying",
  async (status) => {
    const error = {
      stage: "availability",
      message: "Unavailable",
      retryable: false,
      live_analysis: {
        state: "exhausted",
        resets_at: "2026-10-05T00:00:00Z",
      },
      run_artifact_id: null,
    };
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify({ error }), { status }),
      );
    await expect(analyseCase("live")).rejects.toMatchObject({
      error,
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith(
      "/api/showcase/case-01/analysis",
      expect.objectContaining({ method: "POST", body: '{"mode":"live"}' }),
    );
  },
);

test("case requests propagate transport failures without exposing raw responses", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("<html>proxy diagnostics</html>", { status: 502 }),
  );
  const request = getCase();
  await expect(request).rejects.toBeInstanceOf(RequestFailure);
  await expect(request).rejects.toThrow("could not be reached");
});

test("a network failure uses the safe connection failure", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(
    new TypeError("provider connection details"),
  );

  await expect(getCase()).rejects.toMatchObject({
    error: {
      stage: "connection",
      message: expect.stringContaining("could not be reached"),
      retryable: true,
    },
  });
});

test("an unreadable structured error uses the safe connection failure", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ error: { message: "raw provider details" } }), {
      status: 502,
    }),
  );

  await expect(analyseCase("live")).rejects.toMatchObject({
    error: {
      stage: "connection",
      message: expect.stringContaining("could not be reached"),
      retryable: true,
    },
  });
});

test("source loads from the showcase contract", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ title: "Case 01" })),
  );
  await getCase();
  expect(fetcher).toHaveBeenCalledWith("/api/showcase/case-01", undefined);
});
