import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { App } from "../../app/App";

// JSDOM has no layout observer. Browser tests exercise actual graph geometry.
beforeEach(() => vi.stubGlobal("ResizeObserver", class {
  observe() {}
  unobserve() {}
  disconnect() {}
}));
afterEach(() => vi.unstubAllGlobals());

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
const reviewAnalysis = {
  ...analysis,
  graph: {
    entities: [
      { id: "alice", name: "Alice", type: "person" },
      { id: "bob", name: "Bob", type: "person" },
    ],
    relationships: [{ source: "alice", target: "bob", type: "spouse_of", evidence_ids: ["e1", "e2"] }],
    evidence: [
      { id: "e1", document: "source", supporting_text: "Alice and Bob are spouses." },
      { id: "e2", document: "source", supporting_text: "They confirmed their marriage." },
    ],
  },
};
const reviewSource = "Alice and Bob are spouses. They confirmed their marriage.";
function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

test("sample loading is primary and live analysis requires opening its options", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(response(detail));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Authoritative source");
  expect(screen.getByRole("button", { name: "Load sample analysis" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Run live analysis" })).not.toBeVisible();
  await user.click(screen.getAllByRole("link", { name: "Explore the demonstration" })[0]);
  await user.click(screen.getByText("Analysis options"));
  expect(screen.getByRole("button", { name: "Run live analysis" })).toBeEnabled();
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0][0]).toBe("/api/showcase/case-01");
});

test("the embedded relationship list exposes every Evidence choice and exact highlight", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response({ ...detail, source_text: reviewSource }))
    .mockResolvedValueOnce(response(reviewAnalysis));
  const user = userEvent.setup();
  const { container } = render(<App />);
  await user.click(await screen.findByRole("button", { name: "Load sample analysis" }));
  await user.click(await screen.findByText("Relationships as a list"));
  await user.click(screen.getByRole("button", { name: "Review Alice — Spouse of — Bob" }));
  expect(screen.getAllByRole("button", { name: /Evidence \d/ })).toHaveLength(2);
  await user.click(screen.getByRole("button", { name: /Evidence 2/ }));
  expect(container.querySelector("mark")).toHaveTextContent("They confirmed their marriage.");
  expect(screen.getByLabelText("Source document")).toHaveTextContent(reviewSource);
});

test("inline expansion and collapse preserve the result, selected relationship, active Evidence and focus", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response({ ...detail, source_text: reviewSource }))
    .mockResolvedValueOnce(response(reviewAnalysis));
  const user = userEvent.setup();
  const { container } = render(<App />);
  await user.click(await screen.findByRole("button", { name: "Load sample analysis" }));
  await user.click(await screen.findByText("Relationships as a list"));
  const relationship = screen.getByRole("button", { name: "Review Alice — Spouse of — Bob" });
  await user.click(relationship);
  await user.click(screen.getByRole("button", { name: /Evidence 2/ }));
  const source = screen.getByLabelText("Source document");
  const toggle = screen.getByRole("button", { name: "Expand demonstration" });
  toggle.focus();
  await user.keyboard("{Enter}");
  expect(toggle).toHaveAccessibleName("Collapse demonstration");
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(toggle).toHaveFocus();
  expect(relationship).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: /Evidence 2/ })).toHaveAttribute("aria-pressed", "true");
  expect(container.querySelector("mark")).toHaveTextContent("They confirmed their marriage.");
  await user.keyboard("{Enter}");
  expect(toggle).toHaveAccessibleName("Expand demonstration");
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  expect(toggle).toHaveFocus();
  expect(screen.getByLabelText("Source document")).toBe(source);
  expect(relationship).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: /Evidence 2/ })).toHaveAttribute("aria-pressed", "true");
  expect(container.querySelector("mark")).toHaveTextContent("They confirmed their marriage.");
  expect(fetcher).toHaveBeenCalledTimes(2);
});

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
    await userEvent.setup().click(screen.getByText("Analysis options"));
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
    expect(screen.getByRole("button", { name: "Load sample analysis" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Expand demonstration" }));
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

test("source failure leaves the landing routes and explicit reload available", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Network failure"));
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent("The application could not be reached");
  expect(screen.getByRole("button", { name: "Reload case" })).toBeEnabled();
  expect(screen.getByRole("link", { name: "Practitioner application" })).toHaveAttribute("href", "/app");
  expect(screen.queryByRole("button", { name: "Load sample analysis" })).toBeNull();
});

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
    await userEvent.setup().click(screen.getByText("Analysis options"));
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
    await userEvent.setup().click(screen.getByText("Analysis options"));
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
    await userEvent.setup().click(screen.getByText("Analysis options"));
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Run live analysis" }));
  await screen.findByText(/Try live analysis again after/);
  expect(screen.getByRole("button", { name: "Run live analysis" })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Load sample analysis" }));
  await screen.findByText("Sample analysis · Demonstration fixture");
  expect(fetcher.mock.calls[3][1]?.body).toBe('{"mode":"sample"}');
});
