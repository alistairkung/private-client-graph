import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import type { Capabilities, Preview } from "../shared/contracts";
import { Configuration } from "./Configuration";
import { preview } from "./api";

vi.mock("./api", () => ({ preview: vi.fn(), freeze: vi.fn() }));
it("ignores a stale preview after the proposal changes", async () => {
  let resolveOld!: (value: Preview) => void;
  let resolveNew!: (value: Preview) => void;
  vi.mocked(preview)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveOld = resolve;
        }),
    )
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveNew = resolve;
        }),
    );
  const capabilities: Capabilities = {
    api_version: "1",
    live_enabled: false,
    inputs: [],
    models: ["deepseek-flash"],
    provider: "Recorded only",
    fresh_input_id: "case_03_fixture",
    maximum_extraction_samples: 5,
    maximum_resolver_repetitions: 3,
  };
  render(<Configuration capabilities={capabilities} />);
  await waitFor(() => expect(preview).toHaveBeenCalledTimes(1));
  await userEvent.selectOptions(
    screen.getByRole("combobox", { name: "Execution mode", exact: true }),
    "recorded",
  );
  await waitFor(() => expect(preview).toHaveBeenCalledTimes(2));
  const response: Preview = {
    proposal: vi.mocked(preview).mock.calls[1][0],
    inputs: [],
    extraction_call_maximum: 0,
    resolution_call_maximum: 1,
    matrix_call_maximum: 1,
    planned_observations: 2,
    invocation_cap: 1,
    task_paid_usage: 0,
    task_paid_allowance: 0,
    task_paid_remaining: 0,
    cost_reason: "New server preview",
  };
  await act(async () => {
    resolveNew(response);
  });
  expect(
    within(screen.getByRole("region")).getByText("New server preview"),
  ).toBeVisible();
  await act(async () => {
    resolveOld({ ...response, cost_reason: "Stale server preview" });
  });
  expect(screen.queryByText("Stale server preview")).not.toBeInTheDocument();
  expect(screen.getByText("New server preview")).toBeVisible();
});
