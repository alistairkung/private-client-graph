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
const workspace = {
  name: "Research question",
  run_ids: ["first", "unpriced", "empty"],
} as WorkspaceDetail;
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

it("shares input-mode filters across tabs without changing selection or renumbering Runs after a failed read", () => {
  const select = vi.fn();
  const saved = run("saved", 0.5, 0.1),
    fresh = run("fresh", 0.8, 0.2);
  saved.plan.preview.proposal.input_mode = "saved";
  fresh.plan.preview.proposal.input_mode = "fresh";
  const scope = { ...workspace, run_ids: ["unreadable", "saved", "fresh"] };
  const { container } = render(
    <RunChart
      workspace={scope}
      runs={[saved, fresh]}
      selected="saved"
      select={select}
    />,
  );
  expect(
    screen.getByRole("button", { name: /Run 2, F1 0.500/ }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /Run 2 · No resolver/ }),
  ).toBeInTheDocument();
  expect(screen.getByText("Research question · Run 2")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Input mode"), {
    target: { value: "fresh" },
  });
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(
    screen.getByRole("button", { name: /Run 3, F1 0.800/ }),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(screen.getByLabelText("Input mode")).toHaveValue("fresh");
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(
    screen.getByRole("button", { name: /Run 2 · No resolver/ }),
  ).toHaveAttribute("aria-pressed", "true");
  expect(select).not.toHaveBeenCalled();
});

function benchmarkRun(
  id: string,
  {
    cost = 0.027418308,
    currency = "USD",
    origin = "live",
    reasons = [],
    unpriced = 0,
  }: {
    cost?: number | null;
    currency?: string | null;
    origin?: "live" | "offline_fixture";
    reasons?: string[];
    unpriced?: number;
  } = {},
): RunDetail {
  const detail = run(id, 182 / 197, cost);
  detail.evaluation.cost = {
    total: cost,
    known_subtotal: 0.027418308,
    currency,
    attempts: 34,
    unpriced_attempts: unpriced,
    reasons,
  };
  detail.benchmark = {
    scope: { observation_origin: origin },
    cohort: {
      all_condition_micro_f1: 182 / 214,
      valid_graphs: 30,
      planned_conditions: 34,
      outcomes: {},
    },
  } as NonNullable<RunDetail["benchmark"]>;
  return detail;
}

it("plots the imported Protocol v1 score against the verified provider estimate", () => {
  const baseline = benchmarkRun("baseline");
  render(
    <RunChart
      workspace={{ ...workspace, run_ids: [baseline.id] }}
      runs={[baseline]}
      selected={baseline.id}
      select={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(
    screen.getByRole("button", {
      name: /All-condition micro-F1 · Protocol v1 0.850/,
    }),
  ).toBeVisible();
  expect(
    screen.getByText(/Estimated provider spend incurred by Run \(USD\)/),
  ).toBeVisible();
  expect(
    screen.getByText(/Estimated provider spend.*USD 0.027418308/),
  ).toBeVisible();
});

it("plots Protocol v1 zero when all graphs fail and provider cost is verified", () => {
  const failed = benchmarkRun("failed");
  failed.evaluation.aggregate.f1 = null;
  failed.evaluation.eligibility.f1_vs_cost = false;
  if (!failed.benchmark) throw new Error("Expected a Benchmark fixture");
  failed.benchmark.cohort.valid_graphs = 0;
  failed.benchmark.cohort.all_condition_micro_f1 = 0;
  render(
    <RunChart
      workspace={{ ...workspace, run_ids: [failed.id] }}
      runs={[failed]}
      selected={failed.id}
      select={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(
    screen.getByRole("button", {
      name: /Protocol v1 0.000.*0\/34 valid graphs/,
    }),
  ).toBeVisible();
});

it("excludes incomplete, unverified, simulated, and incompatible imported costs", () => {
  const runs = [
    benchmarkRun("verified"),
    benchmarkRun("subtotal-only", { cost: null }),
    benchmarkRun("unpriced", { unpriced: 1 }),
    benchmarkRun("unverified", {
      reasons: ["Authoritative task ledger is unavailable."],
    }),
    benchmarkRun("offline", { origin: "offline_fixture" }),
    benchmarkRun("other-currency", { currency: "EUR" }),
    benchmarkRun("no-currency", { currency: null }),
  ];
  const { container } = render(
    <RunChart
      workspace={{ ...workspace, run_ids: runs.map(({ id }) => id) }}
      runs={runs}
      selected="verified"
      select={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(
    screen.getByText("Authoritative task ledger is unavailable."),
  ).toBeVisible();
  expect(screen.getByText(/EUR.*USD/)).toBeVisible();
});

it("keeps the historical cost axis and uses the visible Benchmark currency after filtering", () => {
  const historical = run("historical", 0.72, 0.1);
  historical.plan.preview.proposal.input_mode = "fresh";
  const benchmark = benchmarkRun("benchmark", { currency: "EUR" });
  benchmark.plan.preview.proposal.input_mode = "saved";
  render(
    <RunChart
      workspace={{ ...workspace, run_ids: [historical.id, benchmark.id] }}
      runs={[historical, benchmark]}
      selected={benchmark.id}
      select={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(screen.getByRole("button", { name: /Run 1, F1 0.720/ })).toBeVisible();
  expect(
    screen.queryByRole("button", { name: /Protocol v1 0.850/ }),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Input mode"), {
    target: { value: "saved" },
  });
  expect(
    screen.getByText(/Estimated provider spend incurred by Run \(EUR\)/),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: /Protocol v1 0.850/ }),
  ).toBeVisible();
});

it("shares the metric across plot modes and omits missing evidence and cost points", () => {
  const first = run("first", 0.9, 0.04);
  const unpriced = run("unpriced", 0.95, null);
  const empty = run("empty", null, 0);
  const score = (f1: number) => ({ counts: { tp: 1, fp: 1, fn: 1 }, precision: 0.5, recall: 0.5, f1 });
  first.quality = {
    version: "evidence_grounded_f1_v1",
    planned_inputs: 35, observed_inputs: 35, qualified_inputs: 34, observed_qualified_inputs: 34,
    outcomes: { scored: 35 }, input_outcomes: {},
    graph: score(0.9), qualified_graph: score(0.88), grounded: score(0.1),
    complete_proof: { complete: 1, targets: 4, rate: 0.25 },
    joint_only_proof: { complete: 0, targets: 1, rate: 0 },
  };
  unpriced.quality = { ...first.quality, grounded: score(0.2) };
  const select = vi.fn();
  const { container } = render(<RunChart workspace={workspace} runs={[first, unpriced, empty]} selected="first" select={select} />);
  const metric = screen.getByRole("combobox", { name: "Metric" });
  fireEvent.change(metric, { target: { value: "grounded" } });
  expect(screen.getByRole("heading", { name: "Evidence-Grounded F1 by Run" })).toBeVisible();
  expect(container.querySelectorAll(".chart-point")).toHaveLength(2);
  expect(screen.getByRole("button", { name: /Run 2, Evidence-Grounded.*20\.00%/ })).toBeVisible();
  fireEvent.click(screen.getByRole("tab", { name: "F1 vs Cost" }));
  expect(metric).toHaveValue("grounded");
  expect(screen.getByRole("heading", { name: "Evidence-Grounded F1 vs Cost" })).toBeVisible();
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(screen.queryByRole("button", { name: /Run 2, Evidence-Grounded/ })).not.toBeInTheDocument();
  fireEvent.change(metric, { target: { value: "proof" } });
  expect(screen.getByRole("button", { name: /Run 1, Complete Proof Rate.*25\.00%.*1\/4/ })).toBeVisible();
  fireEvent.click(screen.getByRole("tab", { name: "F1 by Run" }));
  expect(screen.getByRole("heading", { name: "Complete Proof Rate by Run" })).toBeVisible();
  expect(metric).toHaveValue("proof");
});
