import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { App } from "./App";

const detail = {
  live_analysis: { state: "available", resets_at: null },
  title: "Case 01",
  notice: "Synthetic case",
  source_text: "Authoritative source",
};
const analysis = {
  execution: { mode: "sample", run_artifact_id: null },
  graph: { entities: [], relationships: [], evidence: [] },
};
function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

test.each(["live", "sample"] as const)(
  "%s analysis is explicit, busy, and visibly labelled on success",
  async (mode) => {
    let finish!: (value: Response) => void;
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(detail))
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finish = resolve;
          }),
      )
      .mockResolvedValue(response(detail));
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Authoritative source");
    expect(fetcher).toHaveBeenCalledTimes(1);
    await user.click(
      screen.getByRole("button", {
        name: mode === "live" ? "Run live analysis" : "Load sample analysis",
      }),
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      mode === "live" ? "Running live analysis" : "Loading sample analysis",
    );
    expect(
      screen.getByRole("button", { name: "Run live analysis" }),
    ).toBeDisabled();
    finish(
      response({ ...analysis, execution: { mode, run_artifact_id: null } }),
    );
    await screen.findByText(
      mode === "live"
        ? "Live analysis · Newly extracted"
        : "Sample analysis · Demonstration fixture",
    );
    expect(screen.getByText("No relationships found")).toBeVisible();
    expect(screen.getByLabelText("Source document")).toHaveTextContent(
      "Authoritative source",
    );
  },
);

test.each([
  ["provider", true],
  ["graph", false],
] as const)(
  "error at %s stage only offers explicit applicable recovery",
  async (stage, retryable) => {
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(detail))
      .mockImplementation(async (url) => url === "/api/showcase/case-01" ? response(detail) :
        response(
          { error: { stage, message: "No analysis produced.", retryable } },
          502,
        ),
      );
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Authoritative source");
    await user.click(screen.getByRole("button", { name: "Run live analysis" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No analysis produced.",
    );
    expect(
      screen.queryByRole("button", { name: "Retry live analysis" }) !== null,
    ).toBe(retryable);
    expect(
      screen.getByRole("button", { name: "Load sample analysis" }),
    ).toBeEnabled();
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
    if (retryable) {
      await user.click(
        screen.getByRole("button", { name: "Retry live analysis" }),
      );
      await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(5));
      expect(fetcher.mock.calls[3][1]?.body).toBe('{"mode":"live"}');
    }
  },
);

test.each(["/app", "/app/"])(
  "%s shows an empty practitioner collection without requesting showcase data",
  async (path) => {
    window.history.replaceState(null, "", path);
    const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(response([]));
    render(<App />);
    expect(screen.getByRole("heading", { name: "Matters" })).toBeVisible();
    expect(await screen.findByText("No Matters available")).toBeVisible();
    expect(screen.getByRole("link", { name: "Matters" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Public showcase" })).toHaveAttribute("href", "/");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledWith("/api/matters");
    expect(document.title).toBe("Matters · Private Client Graph");
  },
);

test.each(["disabled", "exhausted", "unavailable"])(
  "%s live availability prevents provider requests while sample still works",
  async (state) => {
    const fetcher = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ ...detail, live_analysis: {
        state, resets_at: state === "exhausted" ? "2026-10-05T00:00:00Z" : null,
      } }))
      .mockResolvedValueOnce(response(analysis));
    render(<App />);
    await screen.findByText("Authoritative source");
    const live = screen.getByRole("button", { name: "Run live analysis" });
    expect(live).toBeDisabled();
    const user = userEvent.setup();
    await user.click(live);
    expect(fetcher).toHaveBeenCalledTimes(1);
    if (state === "exhausted") expect(document.querySelector("time")).toHaveAttribute("dateTime", "2026-10-05T00:00:00Z");
    await user.click(screen.getByRole("button", { name: "Load sample analysis" }));
    await screen.findByText("Sample analysis · Demonstration fixture");
    expect(fetcher.mock.calls[1][1]?.body).toBe('{"mode":"sample"}');
  },
);

test("an authoritative quota rejection refreshes live availability and leaves sample usable", async () => {
  const exhausted = { state: "exhausted", resets_at: "2026-10-05T00:00:00Z" };
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response(detail))
    .mockResolvedValueOnce(response({ error: {
      stage: "availability", message: "Live analysis is unavailable until the next window.",
      retryable: false, live_analysis: exhausted,
    } }, 429))
    .mockResolvedValueOnce(response({ ...detail, live_analysis: exhausted }))
    .mockResolvedValueOnce(response(analysis));
  render(<App />);
  await screen.findByText("Authoritative source");
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Run live analysis" }));
  await screen.findByText(/Try live analysis again after/);
  expect(screen.getByRole("button", { name: "Run live analysis" })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Load sample analysis" }));
  await screen.findByText("Sample analysis · Demonstration fixture");
  expect(fetcher.mock.calls[3][1]?.body).toBe('{"mode":"sample"}');
});
