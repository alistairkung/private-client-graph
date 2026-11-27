import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { BenchmarkV4Summary, BenchmarkV4Comparison, DeliveredGraphMetrics, EvidenceQuality, RunDetail, WorkspaceDetail } from "../shared/contracts";
import { GraphMetrics } from "./BenchmarkV4Summary";
import { RunChart } from "./RunChart";
import { RunQuality, RunQualityComparison } from "./RunQuality";

const graph = (inputs: number, f1: number): DeliveredGraphMetrics => ({
  inputs, valid_graphs: inputs, without_graph: 0, exact_graphs: 0,
  counts: { tp: 0, fp: 0, fn: 0 }, precision: 0, recall: 0, f1, outcomes: {},
});
const quality: EvidenceQuality = {
  version: "deterministic_evidence_quality_v1", state: "complete",
  scope_sha256: "a", scoring_sha256: "b", qualified_reference_sha256: "c",
  observation_origin: "offline_fixture",
  planned_inputs: 35, observed_inputs: 35, qualified_inputs: 34, observed_qualified_inputs: 34,
  expected_relationships: 110, observed_proof_targets: 71, observed_joint_targets: 30,
  combined_graph: graph(35, 0.8),
  qualified_graph: graph(34, 0.75),
  complete_proof: { complete: 21, targets: 71, rate: 21 / 71 },
  joint_only_complete_proof: { complete: 5, targets: 30, rate: 5 / 30 },
  joint_only_coverage: { targets: 30, mean: 0.45 },
};
const provisional: EvidenceQuality = {
  ...quality, state: "provisional", observed_inputs: 1, observed_qualified_inputs: 0,
  observed_proof_targets: 0, observed_joint_targets: 0,
  qualified_graph: null,
  complete_proof: { ...quality.complete_proof, complete: 0, rate: null },
  joint_only_complete_proof: { ...quality.joint_only_complete_proof, complete: 0, rate: null },
  joint_only_coverage: { ...quality.joint_only_coverage, mean: null },
};

function qualityRun(
  id: string,
  value: EvidenceQuality,
  { live = false, unpriced = 0 }: { live?: boolean; unpriced?: number } = {},
): RunDetail {
  return {
    id,
    lifecycle: value.state,
    plan: { preview: { proposal: { resolver: "none", input_mode: "fresh" } } },
    observations: [],
    benchmark_v4: {
      state: value.state, observation_origin: live ? "live" : "offline_fixture",
      combined: value.combined_graph,
    },
    quality: value,
    pipeline_usage: { full_pipeline: { estimated_cost: 0.05, currency: "USD", attempts: 1, unpriced_attempts: unpriced } },
  } as unknown as RunDetail;
}

it("plots reference-rate estimates with the selected quality metric and original Run number", () => {
  const retained = qualityRun("retained", quality, { live: true, unpriced: 1 });
  retained.reference_cost = {
    total: 0.04, currency: "USD", source_url: "https://example.test/pricing", retrieved_at: "2026-11-27",
  };
  const workspace: WorkspaceDetail = {
    api_version: "2", id: "experiment", name: "Synthetic comparison",
    created_at: "2026-11-27", description: null, hypothesis: null,
    draft: { revision: 0, configuration: retained.plan.preview.proposal, copied_from_run: null },
    run_ids: [retained.id], run_numbers: { retained: 3 },
    metadata_available: true, read_only_import: false,
  };
  render(
    <RunChart
      workspace={workspace}
      runs={[retained]} selected={retained.id} select={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByRole("combobox", { name: "Performance metric" }), {
    target: { value: "joint_only_coverage" },
  });
  fireEvent.click(screen.getByRole("tab", { name: "Vs Cost" }));
  expect(screen.getByRole("button", {
    name: /Run 3, Multi-Source Evidence Coverage.*45\.00%/,
  })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByText("Reference-rate estimate · USD 0.0400")).toBeVisible();
});

it("shares the selected quality metric across plots and leaves missing scores and unverifiable costs off the plot", () => {
  const runs = [
    qualityRun("priced", quality, { live: true }),
    qualityRun("provisional", provisional, { live: true }),
    qualityRun("offline", quality),
    qualityRun("unpriced", { ...quality, joint_only_coverage: { targets: 30, mean: 0 } }, { live: true, unpriced: 1 }),
  ];
  const select = vi.fn();
  const { container } = render(
    <RunChart
      workspace={{ name: "Synthetic comparison", run_ids: runs.map((run) => run.id) } as WorkspaceDetail}
      runs={runs} selected="provisional" select={select}
    />,
  );
  const metric = screen.getByRole("combobox", { name: "Performance metric" });
  expect(within(metric).getAllByRole("option").map((option) => option.textContent)).toEqual([
    "Combined Graph F1", "Qualified Graph F1", "Proof Completion", "Multi-Source Evidence Coverage",
  ]);
  expect(screen.getByRole("button", { name: /Run 2, Combined Graph F1 · 35 evaluation inputs.*provisional/ })).toHaveAttribute("aria-pressed", "true");
  fireEvent.change(metric, { target: { value: "qualified_graph" } });
  expect(screen.getByRole("heading", { name: "Qualified Graph F1 by Run" })).toBeVisible();
  expect(screen.getByText("Qualified Graph F1 (%)", { exact: true })).toBeVisible();
  expect(container.querySelectorAll(".chart-point")).toHaveLength(3);
  expect(screen.getByRole("button", { name: /Run 2 · No resolver/ })).toHaveAttribute("aria-pressed", "true");
  fireEvent.change(metric, { target: { value: "joint_only_coverage" } });
  expect(screen.getByRole("button", { name: /Run 4, Multi-Source Evidence Coverage · 30 multi-Source proof targets · qualified cohort 0.00%/ })).toBeVisible();
  fireEvent.keyDown(screen.getByRole("tab", { name: "By Run" }), { key: "ArrowRight" });
  expect(screen.getByRole("tab", { name: "Vs Cost" })).toHaveFocus();
  expect(metric).toHaveValue("joint_only_coverage");
  expect(screen.getByText("Average percentage of required evidence recovered for relationships that need multiple Sources. Uses the best-matching approved proof route.")).toBeVisible();
  expect(screen.getByRole("heading", { name: "Multi-Source Evidence Coverage vs Cost" })).toBeVisible();
  expect(screen.getByText(/Estimated full pipeline cost \(USD\)/)).toBeVisible();
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(screen.getByRole("button", { name: /Run 1, Multi-Source Evidence Coverage.*45.00%/ })).toBeVisible();
  expect(select).not.toHaveBeenCalled();
});

it("keeps unavailable provisional proof scores distinct from zero and exposes fixed denominator counts", () => {
  render(<RunQuality quality={provisional} />);
  expect(screen.getByRole("status")).toHaveTextContent("1 of 35 inputs observed");
  expect(screen.getAllByText("Unavailable", { exact: true })[0]).toBeVisible();
  expect(screen.getByText("80.00%", { exact: true })).toBeVisible();
  expect(screen.getByText(/71 formal proof targets · qualified cohort/)).toBeVisible();
  fireEvent.click(screen.getByText("Evidence metrics and counts"));
  expect(screen.getByText("0 / 71 · 0 targets observed")).toBeVisible();
  expect(screen.getByText("Multi-Source Proof Completion")).toBeVisible();
  expect(screen.getByText("Unavailable · 0 / 30 targets observed")).toBeVisible();
  expect(screen.getByText(/synthetic benchmark measures do not assess legal sufficiency/)).toBeVisible();
});

it("shows scope and both graph metrics in comparisons, with change only when provided", () => {
  const comparison = {
    left_quality: quality, right_quality: provisional, quality_delta: null,
  } as BenchmarkV4Comparison;
  const { rerender } = render(<RunQualityComparison comparison={comparison} />);
  const table = screen.getByRole("table", { name: "Evidence quality comparison" });
  expect(within(table).getByRole("row", { name: /Qualified Graph F1.*75.00%.*34 qualified Conditions.*Unavailable/ })).toBeVisible();
  expect(within(table).getByRole("row", { name: /Combined Graph F1.*35 evaluation inputs · mixed references/ })).toBeVisible();
  expect(within(table).queryByRole("columnheader", { name: "Change" })).not.toBeInTheDocument();
  expect(screen.getByText(/Changes are unavailable/)).toBeVisible();
  rerender(<RunQualityComparison comparison={{
    ...comparison, right_quality: quality,
    quality_delta: { combined_graph: 0, qualified_graph: 0.01, complete_proof: 0, joint_only_coverage: -0.02 },
  }} />);
  expect(within(table).getByRole("columnheader", { name: "Change" })).toBeVisible();
  expect(within(table).getByText("+1.00 pp")).toBeVisible();
  expect(within(table).getByText("-2.00 pp")).toBeVisible();
});

it("uses unavailable qualified scope from quality even if the raw graph projection has zero", () => {
  const summary = { combined: provisional.combined_graph, qualified: graph(34, 0), consensus: null } as BenchmarkV4Summary;
  render(<GraphMetrics summary={summary} quality={provisional} />);
  const row = screen.getByRole("row", { name: /34 qualified Conditions/ });
  expect(within(row).getAllByText("Unavailable").length).toBeGreaterThan(0);
  expect(within(row).queryByText("0.000")).not.toBeInTheDocument();
});
