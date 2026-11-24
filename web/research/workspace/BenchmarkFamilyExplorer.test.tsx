import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type {
  BenchmarkRun,
  FamilyResearchContext,
  RunDetail,
  RunObservation,
} from "../shared/contracts";
import { BenchmarkFamilyExplorer } from "./BenchmarkFamilyExplorer";

function makeRun(
  familyContext: FamilyResearchContext | null = null,
): RunDetail {
  const metrics = {
    planned_conditions: 2,
    valid_graphs: 2,
    exact_graphs: 1,
    construction_success_rate: 1,
    exact_graph_accuracy: 0.5,
    valid_graph_only_exact_accuracy: 0.5,
    all_conditions: { tp: 3, fp: 0, fn: 1 },
    all_condition_micro_f1: 0.857,
    valid_graph_only: { tp: 3, fp: 0, fn: 1 },
    valid_graph_only_micro_f1: 0.857,
    expected_edges_without_graph: 0,
    planned_proofs: 3,
    complete_proofs: 0,
    proof_completion_rate: 0,
    planned_joint_proofs: 1,
    complete_joint_proofs: 0,
    joint_proof_completion_rate: 0,
    incomplete_proofs: 3,
    missed_proofs: 0,
    proofs_without_graph: 0,
    quote_passed: 4,
    quote_assessed: 4,
    attribution_passed: 4,
    attribution_assessed: 4,
    outcomes: {},
  };
  const conditions = [
    { family: "E", condition: "E000", role: "natural" },
    { family: "E", condition: "E001", role: "matched" },
  ].map((item) => ({
    ...item,
    contrast: null,
    outcome: "scored" as const,
    expected: { sources: [], entities: [], relationships: [], evidence: [] },
    expected_edges: 2,
    parsed_prediction: null,
    expected_relationships: [],
    graph: null,
    proof_targets: [],
    metrics: {
      tp: 0,
      fp: 0,
      fn: 0,
      correct_relationships: 0,
      unsupported_relationships: 0,
      missing_relationships: 0,
      complete_proofs: 0,
      planned_proofs: 2,
      complete_joint_proofs: 0,
      planned_joint_proofs: 1,
      incomplete_proofs: 2,
      missed_proofs: 0,
      quote_passed: 0,
      quote_assessed: 0,
      attribution_passed: 0,
      attribution_assessed: 0,
    },
    failure_detail: null,
  }));
  const benchmark = {
    scope: {
      benchmark_sha256: "a".repeat(64),
      protocol_version: "benchmark_v3_evaluation_v1",
      protocol: "Evaluation Protocol v1",
      split: "development",
      observation_origin: "live",
      conditions: [],
    },
    cohort: metrics,
    families: { E: metrics, F: metrics },
    family_macro_f1: 0.857,
    valid_graph_only_family_macro_f1: 0.857,
    valid_graph_only_macro_family_count: 1,
    run_artifact_digest: null,
    observations: conditions,
    scope_identity: "synthetic",
  } as unknown as BenchmarkRun;
  const observations = conditions.map((item, index) => ({
    id: `observation-${index}`,
    sample_id: `sample-${index}`,
    case_id: item.condition,
    configuration: "synthetic",
    repetition: index,
    status: "scored",
    reason: null,
    metadata: null,
    source: null,
    sources: [],
    result: null,
    langfuse_trace_ids: [],
    relationships: [],
    benchmark: item,
  })) as RunObservation[];
  return {
    id: "run",
    experiment_id: "experiment",
    family_context: familyContext
      ? {
          schema_version: 1,
          benchmark_sha256: "a".repeat(64),
          axis_definitions: {
            "contradictory-assertions": "Reconcile conflicting assertions.",
            "origin-and-copies": "Trace the origin of accounts and copies.",
            "evidence-sufficiency": "Decide whether evidence is sufficient.",
          },
          families: { E: familyContext },
        }
      : null,
    benchmark,
    observations,
    evaluation: { cost: { attempts: 0, total: null, currency: null } },
    provenance: {},
    artifact_digest: "b".repeat(64),
  } as unknown as RunDetail;
}

const context: FamilyResearchContext = {
  revision: 1,
  dossier_sha256: "c".repeat(64),
  description: "Reconcile two firsthand accounts of a reported parent relationship.",
  shortcuts: "Counting a forwarded statement as an independent witness.",
  hypothesis_text: "Two independent accounts agree about the same birth.",
  hypothesis_basis: "versioned_hypothesis",
  hypothesis: {
    hypothesis_id: "independent-parentage-disagreement",
    revision: 1,
    hypothesis_sha256: "d".repeat(64),
  },
  primary_axis: "contradictory-assertions",
  secondary_axes: ["origin-and-copies", "evidence-sufficiency"],
  condition_intents: {
    E000: "Two independent accounts agree about the same birth.",
    E001: "One account changes to a denial. The disputed relationship becomes unresolved.",
  },
  verified_findings: [],
  incidental_challenges: [],
  scope_limits: "One fictional file only.",
};

it("keeps all families concise and pairs graph score with proof completion", () => {
  render(
    <BenchmarkFamilyExplorer
      run={makeRun(context)}
      renderCondition={() => null}
    />,
  );

  expect(
    screen.getByText(context.description),
  ).toBeInTheDocument();
  expect(screen.getAllByText("0 of 3 complete")).toHaveLength(2);
  expect(screen.getAllByText("Graph F1")).toHaveLength(2);
  expect(screen.getAllByText("6/7 basis")).toHaveLength(2);
  expect(screen.getAllByText("Complete proofs")).toHaveLength(2);
  expect(screen.getByText("Contradictory Assertions")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Family E/ })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});

it("finds a family from its Environment Condition identifier", () => {
  render(
    <BenchmarkFamilyExplorer
      run={makeRun(context)}
      renderCondition={() => null}
    />,
  );

  fireEvent.change(
    screen.getByRole("searchbox", {
      name: "Find a family or Environment Condition",
    }),
    { target: { value: "E001" } },
  );

  expect(screen.getByRole("button", { name: /Family E/ })).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /Family F/ }),
  ).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /Family E/ }));
  expect(screen.getByRole("tab", { name: /E001/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  fireEvent.click(screen.getByRole("tab", { name: /E000/ }));
  expect(screen.getByRole("tab", { name: /E000/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );

  fireEvent.change(
    screen.getByRole("searchbox", {
      name: "Find a family or Environment Condition",
    }),
    { target: { value: "" } },
  );
  expect(screen.getByRole("tab", { name: /E000/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );

  fireEvent.change(
    screen.getByRole("searchbox", {
      name: "Find a family or Environment Condition",
    }),
    { target: { value: "Contradictory Assertions" } },
  );
  expect(screen.getByRole("button", { name: /Family E/ })).toBeInTheDocument();
});

it("shows the tested hypothesis, declared axes and Environment Condition tabs in place", () => {
  render(
    <BenchmarkFamilyExplorer
      run={makeRun(context)}
      renderCondition={(observation) => (
        <p>Selected {observation.benchmark?.condition}</p>
      )}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: /Family E/ }));

  expect(screen.getByText(/Adversarial Hypothesis/)).toBeInTheDocument();
  expect(screen.getByText(context.shortcuts)).toBeInTheDocument();
  expect(screen.getByText(/Primary difficulty axis/)).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: /Natural/ })).toBeInTheDocument();
  expect(screen.getByText("Matched")).toBeInTheDocument();
  expect(document.querySelector(".condition-intent")).toHaveTextContent(
    "Two independent accounts agree",
  );
  expect(screen.getByText("Selected E000")).toBeInTheDocument();

  fireEvent.keyDown(screen.getByRole("tab", { name: /E000/ }), {
    key: "End",
  });
  expect(screen.getByRole("tab", { name: /E001/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  expect(document.querySelector(".condition-intent")).toHaveTextContent(
    "One account changes to a denial",
  );
  expect(screen.getByText("Selected E001")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /Family F/ }));
  expect(screen.getByRole("button", { name: /Family F/ })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  expect(screen.getByRole("button", { name: /Family E/ })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});

it("keeps research context unavailable when the Run does not carry a verified context", () => {
  render(
    <BenchmarkFamilyExplorer
      run={makeRun()}
      renderCondition={() => null}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: /Family E/ }));
  expect(
    screen.getByRole("status"),
  ).toBeInTheDocument();
});
