import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { DraftEditor } from "./DraftEditor";
import * as api from "./api";
import type { Capabilities, RunDraft, Preview } from "../shared/contracts";
vi.mock("./api", () => ({
  saveDraft: vi.fn(),
  getRun: vi.fn(),
  previewDraft: vi.fn(),
  freezeDraft: vi.fn(),
}));
vi.mock("../configuration/PlanSummary", () => ({
  PlanSummary: () => <p>Server preview</p>,
}));
const draft: RunDraft = {
  revision: 3,
  copied_from_run: null,
  configuration: {
    retained_experiment_id: null,
    retained_run_id: null,
    input_ids: ["case_01_fixture", "case_03_fixture"],
    input_mode: "saved",
    execution_mode: "recorded",
    resolver: "generative",
    extraction_samples: 1,
    resolver_repetitions: 1,
    invocation_cap: 1,
    task_call_cap: 0,
    temperature: null,
    timeout_seconds: 90,
    model: "deepseek-flash",
  },
};
const capabilities: Capabilities = {
  api_version: "1",
  inputs: [],
  fresh_input_id: "case_03_fixture",
  maximum_extraction_samples: 5,
  maximum_resolver_repetitions: 3,
  models: ["deepseek-flash"],
  provider: "Recorded",
  live_enabled: false,
  live_reason: "Disabled",
  live_task: null,
};
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.previewDraft).mockResolvedValue({
    proposal: draft.configuration,
  } as Preview);
  vi.mocked(api.saveDraft).mockImplementation(async (_id, command) => ({
    revision: command.expected_revision + 1,
    configuration: command.configuration,
    copied_from_run: null,
  }));
});
it("opening a persisted draft is read-only; changing input mode preserves selected cases and saves the next draft only", async () => {
  render(
    <DraftEditor
      id="experiment"
      draft={draft}
      cases={[]}
      capabilities={capabilities}
      saved={() => {}}
      saving={() => {}}
      frozen={() => {}}
    />,
  );
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Run" })).toBeEnabled(),
  );
  expect(api.saveDraft).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: /Extract relationships/ }),
  );
  fireEvent.change(screen.getByRole("combobox", { name: "Input mode" }), {
    target: { value: "fresh" },
  });
  await waitFor(() =>
    expect(api.saveDraft).toHaveBeenCalledWith(
      "experiment",
      expect.objectContaining({
        expected_revision: 3,
        configuration: expect.objectContaining({
          input_mode: "fresh",
          input_ids: draft.configuration.input_ids,
        }),
      }),
    ),
  );
  expect(api.freezeDraft).not.toHaveBeenCalled();
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Run" })).toBeEnabled(),
  );
  fireEvent.click(screen.getByRole("button", { name: "Run" }));
  expect(screen.getByRole("dialog", { name: "Review next Run" })).toBeVisible();
  expect(api.freezeDraft).not.toHaveBeenCalled();
});

it("dismisses the compact insertion menu with Escape or outside click and preserves expanded resolver fields", async () => {
  render(
    <DraftEditor
      id="experiment"
      draft={{
        ...draft,
        configuration: { ...draft.configuration, resolver: "none" },
      }}
      cases={[]}
      capabilities={capabilities}
      saved={() => {}}
      saving={() => {}}
      frozen={() => {}}
    />,
  );
  const add = screen.getByRole("button", {
    name: "Add alias resolution",
  });
  fireEvent.click(add);
  const insert = screen.getByRole("button", {
    name: "Add generative resolver",
  });
  expect(screen.queryByText("After extraction")).not.toBeInTheDocument();
  fireEvent.keyDown(insert, { key: "Escape" });
  expect(add).toHaveFocus();
  expect(
    screen.queryByRole("button", {
      name: "Add generative resolver",
    }),
  ).not.toBeInTheDocument();
  fireEvent.click(add);
  fireEvent.pointerDown(document.body);
  expect(add).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(add);
  fireEvent.click(
    screen.getByRole("button", {
      name: "Add generative resolver",
    }),
  );
  expect(
    screen.getByRole("region", { name: "Resolve aliases settings" }),
  ).toBeVisible();
  expect(screen.getByRole("combobox", { name: "Model" })).toBeVisible();
  expect(
    screen.getByRole("spinbutton", { name: "Temperature (optional)" }),
  ).toBeVisible();
  expect(
    screen.getByRole("spinbutton", { name: "Provider timeout (seconds)" }),
  ).toBeVisible();
  expect(
    screen.getByRole("spinbutton", { name: "Invocation attempt cap" }),
  ).toBeVisible();
});

it("selecting retained outputs saves exact observed identities as a zero-call control", async () => {
  vi.mocked(api.getRun).mockResolvedValue({
    lifecycle: "complete",
    plan: { preview: { proposal: { input_mode: "fresh", resolver: "none" } } },
    observations: [{ sample_id: "case_01_fixture_fresh_01" }],
  } as Awaited<ReturnType<typeof api.getRun>>);
  render(<DraftEditor id="experiment" draft={draft} cases={[]} capabilities={capabilities}
    runIds={["baseline"]} saved={() => {}} saving={() => {}} frozen={() => {}} />);
  fireEvent.change(screen.getByRole("combobox", { name: "Input origin" }), {
    target: { value: "baseline" },
  });
  await waitFor(() => expect(api.saveDraft).toHaveBeenCalledWith("experiment",
    expect.objectContaining({ configuration: expect.objectContaining({
      retained_run_id: "baseline", retained_experiment_id: "experiment",
      input_ids: ["case_01_fixture_fresh_01"], input_mode: "saved",
      resolver: "none", execution_mode: "replay", invocation_cap: 0,
    }) })));
  expect(api.freezeDraft).not.toHaveBeenCalled();
});

it("rejects an unfinished retained Run without replacing the saved draft", async () => {
  vi.mocked(api.getRun).mockResolvedValue({
    lifecycle: "running",
    plan: { preview: { proposal: { input_mode: "fresh", resolver: "none" } } },
    observations: [{ sample_id: "case_01_fixture_fresh_01" }],
  } as Awaited<ReturnType<typeof api.getRun>>);
  render(<DraftEditor id="experiment" draft={draft} cases={[]} capabilities={capabilities}
    runIds={["unfinished"]} saved={() => {}} saving={() => {}} frozen={() => {}} />);
  fireEvent.change(screen.getByRole("combobox", { name: "Input origin" }), {
    target: { value: "unfinished" },
  });
  await screen.findByText("Select a completed fresh no-resolution Run.");
  expect(api.saveDraft).not.toHaveBeenCalled();
  expect(api.freezeDraft).not.toHaveBeenCalled();
});
