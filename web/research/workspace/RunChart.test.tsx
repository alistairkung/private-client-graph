import { render, screen, fireEvent } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { RunDetail, WorkspaceDetail } from "../shared/contracts";
import { RunChart } from "./RunChart";

function run(
  id: string,
  f1: number | null,
  cost: number | null,
  state = "complete",
): RunDetail {
  return {
    id,
    lifecycle: "complete",
    plan: { preview: { proposal: { resolver: "none" } } },
    observations: [],
    evaluation: {
      aggregate: {
        f1,
        state,
        tp: 999,
        fp: 999,
        fn: 999,
        coverage: { scored: f1 === null ? 0 : 1, planned: 2 },
      },
      cost: { total: cost, currency: "USD" },
      eligibility: {
        f1_by_run: f1 !== null,
        f1_vs_cost: f1 !== null && cost !== null,
        f1_reasons: ["No scored observations"],
        cost_reasons: ["Unpriced attempt"],
      },
    },
  } as unknown as RunDetail;
}
const workspace = { name: "Research question" } as WorkspaceDetail;
it("displays server scores including zero, excludes unavailable values, preserves selection and updates a provisional point in place", () => {
  const select = vi.fn();
  const first = run("first", 0, 0, "provisional");
  const unpriced = run("unpriced", 0.72, null);
  const empty = run("empty", null, 0, "unavailable");
  const { rerender, container } = render(
    <RunChart
      workspace={workspace}
      runs={[first, unpriced, empty]}
      selected="first"
      select={select}
    />,
  );
  expect(container.querySelectorAll(".chart-point")).toHaveLength(2);
  expect(
    screen.getByRole("button", {
      name: "Run 1, F1 0.000, provisional, 1/2 scored",
    }),
  ).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(screen.getAllByText("Unpriced attempt")).toHaveLength(2);
  fireEvent.click(screen.getByRole("button", { name: /Run 2 · No resolver/ }));
  expect(select).toHaveBeenCalledWith("unpriced");
  rerender(
    <RunChart
      workspace={workspace}
      runs={[run("first", 0.123, 0), unpriced, empty]}
      selected="first"
      select={select}
    />,
  );
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(
    screen.getByRole("button", {
      name: "Run 1, F1 0.123, complete, 1/2 scored",
    }),
  ).toBeInTheDocument();
  // Deliberately inconsistent counts prove React never recalculates F1.
});
