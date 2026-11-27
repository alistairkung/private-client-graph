import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { BenchmarkV4Summary, DeliveredGraphMetrics, EvidenceQuality, RunDetail, WorkspaceDetail } from "../shared/contracts";
import { GraphMetrics } from "./BenchmarkV4Summary";
import { RunChart } from "./RunChart";
import { PCGEvaluation } from "./PCGEvaluation";

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
    target: { value: "qualified_graph" },
  });
  fireEvent.click(screen.getByRole("tab", { name: "Vs Cost" }));
  expect(screen.getByRole("button", {
    name: /Run 3, Qualified Graph F1.*75\.00%/,
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
    "Qualified Graph F1", "Combined Graph F1",
  ]);
  fireEvent.change(metric, { target: { value: "combined_graph" } });
  expect(screen.getByRole("button", { name: /Run 2, Combined Graph F1 · 35 evaluation inputs.*provisional/ })).toHaveAttribute("aria-pressed", "true");
  fireEvent.change(metric, { target: { value: "qualified_graph" } });
  expect(screen.getByRole("heading", { name: "Qualified Graph F1 by Run" })).toBeVisible();
  expect(screen.getByText("Qualified Graph F1 (%)", { exact: true })).toBeVisible();
  expect(container.querySelectorAll(".chart-point")).toHaveLength(3);
  expect(screen.getByRole("button", { name: /Run 2 · No resolver/ })).toHaveAttribute("aria-pressed", "true");
  fireEvent.keyDown(screen.getByRole("tab", { name: "By Run" }), { key: "ArrowRight" });
  expect(screen.getByRole("tab", { name: "Vs Cost" })).toHaveFocus();
  expect(metric).toHaveValue("qualified_graph");
  expect(screen.getByRole("heading", { name: "Qualified Graph F1 vs Cost" })).toBeVisible();
  expect(screen.getByText(/Estimated full pipeline cost \(USD\)/)).toBeVisible();
  expect(container.querySelectorAll(".chart-point")).toHaveLength(1);
  expect(screen.getByRole("button", { name: /Run 1, Qualified Graph F1.*75.00%/ })).toBeVisible();
  expect(select).not.toHaveBeenCalled();
});

it("shows one provisional evaluation with five unavailable values before qualified observations", () => {
  render(<PCGEvaluation run={qualityRun("provisional", provisional)} expectedEdgesWithoutGraph={0} />);
  expect(screen.getByRole("heading", { name: "PCG Evaluation" })).toBeVisible();
  expect(screen.getByRole("status")).toHaveTextContent("Evaluation is provisional");
  for (const label of ["Graph F1", "Evidence-Adjusted F1", "Evidence Support", "Proof Completion", "Multi-Source Evidence Coverage"]) {
    expect(screen.getByText(label, { exact: true })).toBeVisible();
  }
  expect(screen.getAllByText("Unavailable", { exact: true })).toHaveLength(5);
});

it("uses unavailable qualified scope from quality even if the raw graph projection has zero", () => {
  const summary = { combined: provisional.combined_graph, qualified: graph(34, 0), consensus: null } as BenchmarkV4Summary;
  render(<GraphMetrics summary={summary} quality={provisional} />);
  const row = screen.getByRole("row", { name: /34 qualified Conditions/ });
  expect(within(row).getAllByText("Unavailable").length).toBeGreaterThan(0);
  expect(within(row).queryByText("0.000")).not.toBeInTheDocument();
});
