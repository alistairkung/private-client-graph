import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import type { BenchmarkV4Summary, DeliveredGraphMetrics, EvidenceQuality, RunDetail, SemanticRunSummary, SemanticSummary, WorkspaceDetail } from "../shared/contracts";
import { GraphMetrics } from "./BenchmarkV4Summary";
import { RunChart } from "./RunChart";
import { PCGEvaluation } from "./PCGEvaluation";
import { getEvaluationSummary } from "./api";

vi.mock("./api", () => ({ getEvaluationSummary: vi.fn() }));
const readSummary = vi.mocked(getEvaluationSummary);
beforeEach(() => readSummary.mockReset());

function scoreSummary(
  runId: string,
  f1: number,
  state: SemanticRunSummary["state"] = "complete",
  targets: Partial<SemanticSummary> = {},
): SemanticRunSummary {
  return {
    run_id: runId, state, plan_sha256: null, operations: null,
    graph_f1: graph(34, 0.75),
    evidence_adjusted_f1: {
      f1, incomplete_recovered_proofs: 10, penalty_units: 6.28,
      weight_numerator: 71, weight_denominator: 113, proofs_completed_by_equivalence: 0,
    },
    target_summary: {
      formal_targets: 71, semantic_outcomes: {}, pair_verdicts: {}, candidate_pairs: 0,
      evidence_support: { count: 20, targets: 71, rate: 20 / 71 },
      proof_completion: { count: 15, targets: 71, rate: 15 / 71 },
      multi_source_evidence_coverage: { matched_target_equivalents: 0.8, targets: 30, mean: 0.8 / 30 },
      exact_matched_members: 0, unmatched_required_members: 0, targets_with_added_matches: 0,
      additional_matched_members: 0, newly_completed_proofs: 0,
      ...targets,
    },
  };
}

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
      scope_sha256: "private-scope-hash", scoring_sha256: "private-scoring-hash",
      combined: value.combined_graph,
    },
    quality: value,
    pipeline_usage: { full_pipeline: { estimated_cost: 0.05, currency: "USD", attempts: 1, unpriced_attempts: unpriced } },
  } as unknown as RunDetail;
}

it("plots both scores against a reference-rate estimate with the original Run number", async () => {
  const retained = qualityRun("private-run-id", quality, { live: true, unpriced: 1 });
  retained.reference_cost = {
    total: 0.04, currency: "USD", source_url: "https://example.test/pricing", retrieved_at: "2026-11-27",
  };
  readSummary.mockResolvedValue(scoreSummary(retained.id, 0.62, "exact_only"));
  const workspace: WorkspaceDetail = {
    api_version: "2", id: "experiment", name: "Synthetic comparison",
    created_at: "2026-11-27", description: null, hypothesis: null,
    draft: { revision: 0, configuration: retained.plan.preview.proposal, copied_from_run: null },
    run_ids: [retained.id], run_numbers: { [retained.id]: 3 },
    metadata_available: true, read_only_import: false,
  };
  render(
    <RunChart
      workspace={workspace}
      runs={[retained]} selected={retained.id} select={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByRole("combobox", { name: "Graph metric" }), {
    target: { value: "qualified_graph" },
  });
  fireEvent.click(screen.getByRole("tab", { name: "Vs Cost" }));
  expect(screen.getByRole("button", {
    name: /Run 3, Qualified Graph F1.*75\.00%/,
  })).toHaveAttribute("aria-pressed", "true");
  const adjusted = await screen.findByRole("button", { name: /Run 3, Evidence-Adjusted F1.*62\.00%.*Exact-only/ });
  expect(adjusted).toHaveAttribute("aria-pressed", "true");
  expect(adjusted.style.left).toBe(screen.getByRole("button", { name: /Run 3, Qualified Graph F1/ }).style.left);
  const chart = screen.getByRole("region", { name: "Run history and performance" });
  expect(within(chart).getByText(/Reference-rate estimates use retained token usage/)).toBeVisible();
  expect(chart).not.toHaveTextContent(/private-(run-id|scope-hash|scoring-hash)/);
  const row = within(screen.getByRole("table", { name: "Run scores and cost estimates" })).getByRole("row", { name: /Run 3/ });
  expect(within(row).getAllByRole("cell").map(cell => cell.textContent)).toEqual(["75.00%", "62.00%Exact-only", "0.0400"]);
});

it("keeps both plots in sync while filtering, changing axes and switching graph metrics", async () => {
  const runs = [
    qualityRun("priced", quality, { live: true }),
    qualityRun("provisional", provisional, { live: true }),
    qualityRun("offline", quality),
    qualityRun("unpriced", { ...quality, joint_only_coverage: { targets: 30, mean: 0 } }, { live: true, unpriced: 1 }),
  ];
  runs[2].plan.preview.proposal.input_mode = "saved";
  readSummary.mockImplementation(async (id) => {
    if (id === "offline") throw new Error("Cannot read the retained assessment");
    return scoreSummary(id, id === "priced" ? 0 : 0.62, id === "priced" ? "complete" : "pending");
  });
  const select = vi.fn();
  const { rerender } = render(
    <RunChart
      workspace={{ name: "Synthetic comparison", run_ids: runs.map((run) => run.id) } as WorkspaceDetail}
      runs={runs} selected="provisional" select={select}
    />,
  );
  const metric = screen.getByRole("combobox", { name: "Graph metric" });
  expect(within(metric).getAllByRole("option").map((option) => option.textContent)).toEqual([
    "Combined Graph F1", "Qualified Graph F1",
  ]);
  expect(metric).toHaveValue("combined_graph");
  expect(screen.getByRole("button", { name: /Run 2, Combined Graph F1 · 35 evaluation inputs.*provisional/ })).toHaveAttribute("aria-pressed", "true");
  const evidence = within(screen.getByRole("figure", { name: "Evidence-Adjusted F1" }));
  const adjusted = await evidence.findByRole("button", { name: /Run 1, Evidence-Adjusted F1.*0\.00%/ });
  expect(evidence.getByRole("button", { name: /Run 4, Evidence-Adjusted F1.*62\.00%.*Evaluation pending/ })).toBeVisible();
  expect(evidence.queryByRole("button", { name: /^Run [23],/ })).not.toBeInTheDocument();
  expect(readSummary.mock.calls.map(([id]) => id)).toEqual(["priced", "offline", "unpriced"]);

  fireEvent.change(metric, { target: { value: "qualified_graph" } });
  const graphPlot = within(screen.getByRole("figure", { name: "Qualified Graph F1" }));
  expect(graphPlot.getAllByRole("button")).toHaveLength(3);
  fireEvent.keyDown(screen.getByRole("tab", { name: "By Run" }), { key: "ArrowRight" });
  expect(screen.getByRole("tab", { name: "Vs Cost" })).toHaveFocus();
  expect(metric).toHaveValue("qualified_graph");
  expect(select).not.toHaveBeenCalled();
  expect(screen.getAllByText("Estimated full pipeline cost (USD)")).toHaveLength(2);
  expect(graphPlot.getAllByRole("button")).toHaveLength(1);
  expect(evidence.getAllByRole("button")).toHaveLength(1);
  expect(screen.getByText("Cost exclusions")).toBeVisible();
  expect(screen.getByText(/Run 4 · F1 vs Cost needs complete provider token usage/)).not.toBeVisible();
  fireEvent.click(adjusted);
  expect(select).toHaveBeenCalledWith("priced");
  rerender(<RunChart workspace={{ name: "Synthetic comparison", run_ids: runs.map((run) => run.id) } as WorkspaceDetail}
    runs={[...runs]} selected="priced" select={select} />);
  expect(graphPlot.getByRole("button", { pressed: true })).toBeVisible();
  expect(evidence.getByRole("button", { pressed: true })).toBeVisible();
  const table = within(screen.getByRole("table", { name: "Run scores and cost estimates" }));
  expect(table.getByRole("button", { name: /Run 1 No resolver/, pressed: true })).toBeVisible();
  expect(readSummary).toHaveBeenCalledTimes(3);

  fireEvent.change(screen.getByRole("combobox", { name: "Input mode" }), { target: { value: "saved" } });
  expect(table.getAllByRole("row")).toHaveLength(2);
  expect(table.getByRole("row", { name: /Run 3/ })).toHaveTextContent("Unavailable");
  expect(evidence.getByRole("status")).toHaveTextContent("No Evidence-Adjusted F1 scores");
  readSummary.mockResolvedValue(scoreSummary("offline", 0.71));
  fireEvent.click(screen.getByRole("button", { name: "Refresh evidence scores" }));
  await waitFor(() => expect(table.getByRole("row", { name: /Run 3/ })).toHaveTextContent("71.00%"));
  expect(evidence.queryByRole("button")).not.toBeInTheDocument();
});

it("plots retained evidence rates and their bases across tabs without resetting the comparison", async () => {
  const fresh = qualityRun("fresh", quality, { live: true });
  const saved = qualityRun("saved", quality, { live: true });
  saved.plan.preview.proposal.input_mode = "saved";
  readSummary.mockImplementation(async id => id === fresh.id
    ? scoreSummary(id, 0.62, "exact_only", {
      evidence_support: { count: 0, targets: 71, rate: 0 },
      proof_completion: { count: 0, targets: 71, rate: null },
    })
    : scoreSummary(id, 0.66, "complete"));

  render(<RunChart workspace={{ name: "Synthetic comparison", run_ids: [fresh.id, saved.id] } as WorkspaceDetail}
    runs={[fresh, saved]} selected={fresh.id} select={vi.fn()} />);
  const tabs = within(screen.getByRole("tablist", { name: "Performance metrics" }));
  const f1 = tabs.getByRole("tab", { name: "F1 scores" });
  expect(f1).toHaveAttribute("aria-selected", "true");
  fireEvent.change(screen.getByRole("combobox", { name: "Graph metric" }), { target: { value: "qualified_graph" } });
  fireEvent.click(screen.getByRole("tab", { name: "Vs Cost" }));
  fireEvent.keyDown(f1, { key: "ArrowRight" });
  expect(tabs.getByRole("tab", { name: "Evidence Support" })).toHaveFocus();
  const support = within(screen.getByRole("figure", { name: "Evidence Support" }));
  expect(await support.findByRole("button", { name: /Run 1.*0\.00%.*0 of 71 formal targets.*Exact-only/ }))
    .toHaveAttribute("aria-pressed", "true");
  expect(support.getByRole("button", { name: /Run 2.*28\.17%.*20 of 71.*Exact and equivalent/ })).toBeVisible();
  expect(screen.queryByRole("combobox", { name: "Graph metric" })).not.toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Vs Cost" })).toHaveAttribute("aria-selected", "true");
  const table = within(screen.getByRole("table", { name: "Run scores and cost estimates" }));
  expect(table.getByRole("row", { name: /Run 2/ })).toHaveTextContent("20 of 71 formal targets");

  fireEvent.keyDown(tabs.getByRole("tab", { name: "Evidence Support" }), { key: "ArrowRight" });
  const proof = within(screen.getByRole("figure", { name: "Proof Completion" }));
  expect(proof.queryByRole("button", { name: /Run 1/ })).not.toBeInTheDocument();
  expect(proof.getByRole("button", { name: /Run 2.*21\.13%.*15 of 71/ })).toBeVisible();
  expect(table.getByRole("row", { name: /Run 1/ })).toHaveTextContent("Unavailable");

  fireEvent.change(screen.getByRole("combobox", { name: "Input mode" }), { target: { value: "fresh" } });
  expect(proof.getByRole("status")).toHaveTextContent("No Proof Completion scores are available to plot.");
  fireEvent.keyDown(tabs.getByRole("tab", { name: "Proof Completion" }), { key: "End" });
  const coverage = within(screen.getByRole("figure", { name: "Multi-Source Evidence Coverage" }));
  expect(coverage.getByRole("button", { name: /Run 1.*2\.67%.*0\.8 of 30 target-equivalents/ })).toBeVisible();
  expect(coverage.getByText("Exact-only evaluation")).toBeVisible();
  expect(table.getByRole("row", { name: /Run 1/ })).not.toHaveTextContent("Exact-only");
  expect(table.queryByRole("row", { name: /Run 2/ })).not.toBeInTheDocument();

  fireEvent.keyDown(tabs.getByRole("tab", { name: "Multi-Source Evidence Coverage" }), { key: "Home" });
  expect(f1).toHaveFocus();
  expect(screen.getByRole("combobox", { name: "Graph metric" })).toHaveValue("qualified_graph");
  expect(screen.getByRole("combobox", { name: "Input mode" })).toHaveValue("fresh");
  expect(screen.getByRole("tab", { name: "Vs Cost" })).toHaveAttribute("aria-selected", "true");
  expect(readSummary).toHaveBeenCalledTimes(2);
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
