import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { RunExecution } from "./RunExecution";
import type { ExecutionAvailability, RunDetail } from "../shared/contracts";
import * as api from "./api";
vi.mock("./api", () => ({ authorizeRun: vi.fn(), controlRun: vi.fn() }));
vi.mock("../configuration/PlanSummary", () => ({
  PlanSummary: () => <p>Frozen server preview</p>,
}));
const run = {
  id: "run",
  experiment_id: "experiment",
  lifecycle: "frozen",
  plan: {
    digest: "digest",
    preview: {
      proposal: { execution_mode: "live", task_call_cap: 4, input_ids: [] },
      invocation_cap: 2,
    },
  },
} as unknown as RunDetail;
const availability: ExecutionAvailability = {
  active_run_id: null,
  accounting_reason: null,
  task_budget: {
    task_id: "task",
    label: "Task",
    used: 1,
    cap: 4,
    remaining: 3,
  },
};
beforeEach(() => vi.resetAllMocks());
it("requires explicit approval, authorizes without dispatch and uses that invocation for a separate start", async () => {
  vi.mocked(api.authorizeRun).mockResolvedValue({
    authorized: true,
    started: false,
    invocation_id: "approved-invocation",
  });
  const refresh = vi.fn();
  render(
    <RunExecution
      number={2}
      initiallyOpen
      run={run}
      availability={availability}
      refresh={refresh}
    />,
  );
  expect(
    screen.getByRole("button", { name: "Authorize invocation" }),
  ).toBeDisabled();
  expect(
    screen.queryByRole("button", { name: "Start Run" }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Authorize invocation" }));
  await screen.findByRole("button", { name: "Start Run" });
  expect(api.controlRun).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Start Run" }));
  await waitFor(() =>
    expect(api.controlRun).toHaveBeenCalledWith("experiment", "run", "start", {
      request_id: "approved-invocation",
      plan_digest: "digest",
    }),
  );
});
it("honors global active-run exclusion and displays rejected commands without retrying", async () => {
  const offline = {
    ...run,
    plan: {
      ...run.plan,
      preview: {
        ...run.plan.preview,
        proposal: {
          ...run.plan.preview.proposal,
          execution_mode: "replay" as const,
        },
      },
    },
  };
  const { rerender } = render(
    <RunExecution
      number={2}
      initiallyOpen
      run={offline}
      availability={{ ...availability, active_run_id: "other" }}
      refresh={() => {}}
    />,
  );
  expect(screen.getByRole("button", { name: "Start Run" })).toBeDisabled();
  rerender(
    <RunExecution
      number={2}
      initiallyOpen
      run={offline}
      availability={availability}
      refresh={() => {}}
    />,
  );
  vi.mocked(api.controlRun).mockRejectedValue(new Error("Task budget changed"));
  fireEvent.click(screen.getByRole("button", { name: "Start Run" }));
  await screen.findByRole("alert");
  expect(screen.getByRole("alert")).toHaveTextContent("Task budget changed");
  expect(api.controlRun).toHaveBeenCalledTimes(1);
});

it("reopens a frozen Run without dispatching and preserves authorization when its modal is dismissed", async () => {
  vi.mocked(api.authorizeRun).mockResolvedValue({
    authorized: true,
    started: false,
    invocation_id: "retained-approval",
  });
  render(
    <RunExecution
      number={2}
      run={run}
      availability={availability}
      refresh={() => {}}
    />,
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Review frozen Run" }));
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Authorize invocation" }));
  await screen.findByRole("button", { name: "Start Run" });
  fireEvent.click(screen.getByRole("button", { name: "Close review" }));
  expect(api.controlRun).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Review frozen Run" }));
  fireEvent.click(screen.getByRole("button", { name: "Start Run" }));
  await waitFor(() =>
    expect(api.controlRun).toHaveBeenCalledWith("experiment", "run", "start", {
      request_id: "retained-approval",
      plan_digest: "digest",
    }),
  );
});
