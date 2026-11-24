import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { CanonicalState, RunObservation } from "../shared/contracts";
import { ConditionInspection } from "./ConditionInspection";

vi.mock("../../src/features/review/GraphDrawing", () => ({
  GraphDrawing: ({
    state,
    outcomes,
    alignTo,
    onSelect,
  }: {
    state: CanonicalState;
    outcomes?: Array<string | undefined>;
    alignTo?: CanonicalState;
    onSelect: (index: number, trigger?: HTMLButtonElement) => void;
  }) => (
    <div data-testid={alignTo ? "aligned-graph" : "graph-drawing"}>
      {state.relationships.map((relationship, index) => (
        <button key={index} onClick={(event) => onSelect(index, event.currentTarget)}>
          {relationship.type} · {outcomes?.[index] ?? "unlabelled"}
        </button>
      ))}
    </div>
  ),
}));

vi.mock("./RelationshipEvidence", () => ({
  RelationshipEvidence: ({ edge }: { edge: [string, string, string] }) => (
    <p>Evidence for {edge.join(" · ")}</p>
  ),
}));

const expected: CanonicalState = {
  sources: [],
  evidence: [],
  entities: [
    { id: "expected-a", name: "Ada", type: "person" },
    { id: "expected-b", name: "Bela", type: "person" },
    { id: "expected-c", name: "Cam", type: "person" },
  ],
  relationships: [
    { source: "expected-a", type: "parent_of", target: "expected-b", evidence_ids: [] },
    { source: "expected-b", type: "spouse_of", target: "expected-c", evidence_ids: [] },
  ],
};

const predicted: CanonicalState = {
  sources: [],
  evidence: [],
  entities: [
    { id: "predicted-a", name: "Ada", type: "person" },
    { id: "predicted-b", name: "Bela", type: "person" },
    { id: "predicted-c", name: "Cam", type: "person" },
  ],
  relationships: [
    { source: "predicted-a", type: "parent_of", target: "predicted-b", evidence_ids: [] },
    { source: "predicted-a", type: "spouse_of", target: "predicted-c", evidence_ids: [] },
  ],
};

const observation = (overrides: Record<string, unknown> = {}) => ({
  id: "condition-e000",
  relationships: [
    { id: "r1", edge: ["Ada", "parent_of", "Bela"], outcome: "provenance_failure", expected: [], predicted: [] },
    { id: "r2", edge: ["Bela", "spouse_of", "Cam"], outcome: "missing", expected: [], predicted: [] },
    { id: "r3", edge: ["Ada", "spouse_of", "Cam"], outcome: "extra", expected: [], predicted: [] },
  ],
  benchmark: {
    family: "Q",
    condition: "Q000",
    contrast: null,
    role: "natural",
    outcome: "scored",
    expected,
    expected_edges: 2,
    parsed_prediction: null,
    expected_relationships: [
      { edge: ["Ada", "parent_of", "Bela"], quotes: [] },
      { edge: ["Bela", "spouse_of", "Cam"], quotes: [] },
    ],
    graph: null,
    proof_targets: [],
    metrics: {},
    failure_detail: null,
  },
  result: { state: predicted },
  reason: null,
  ...overrides,
}) as unknown as RunObservation;

it("shows correct, missing, and unsupported outcomes and selects by semantic edge", () => {
  render(<ConditionInspection runId="run-1" observation={observation()} />);

  const expectedGraph = screen.getByRole("region", { name: "Expected graph" });
  const predictedGraph = screen.getByRole("region", { name: "Predicted graph" });
  expect(within(expectedGraph).getByRole("button", { name: /parent_of · correct/ })).toBeTruthy();
  expect(within(expectedGraph).getByRole("button", { name: /spouse_of · missing/ })).toBeTruthy();
  expect(within(predictedGraph).getByRole("button", { name: /spouse_of · unsupported/ })).toBeTruthy();
  const legend = screen.getByRole("group", { name: "Relationship outcomes" });
  expect(within(legend).getByText(/Correct/)).toBeTruthy();
  expect(within(legend).getByText(/Missing/)).toBeTruthy();
  expect(within(legend).getByText(/Unsupported/)).toBeTruthy();

  fireEvent.click(within(predictedGraph).getByRole("button", { name: /spouse_of · unsupported/ }));
  expect(screen.getByRole("region", { name: "Selected relationship evidence" }))
    .toHaveTextContent("Ada · spouse_of · Cam");
});

it("keeps an empty constructed prediction distinct from a missing relationship", () => {
  const emptyPrediction: CanonicalState = {
    sources: [], entities: [], relationships: [], evidence: [],
  };
  render(
    <ConditionInspection
      runId="run-1"
      observation={observation({ result: { state: emptyPrediction }, relationships: [
        { id: "r2", edge: ["Bela", "spouse_of", "Cam"], outcome: "missing", expected: [], predicted: [] },
      ] })}
    />,
  );
  expect(within(screen.getByRole("region", { name: "Predicted graph" }))
    .getByText("Valid empty graph")).toBeTruthy();
  expect(within(screen.getByRole("group", { name: "Relationship outcomes" }))
    .getByText(/Missing/)).toBeTruthy();
  expect(screen.queryByText("Prediction unavailable")).toBeNull();
});

it("shows only expected relationships and preserves their inspection on construction failure", () => {
  render(
    <ConditionInspection
      runId="run-1"
      observation={observation({
        reason: "Candidate source quote failed validation.",
        result: { state: null },
        relationships: [
          { id: "placeholder", edge: ["Ada", "parent_of", "Bela"], outcome: "missing", expected: [], predicted: [] },
        ],
        benchmark: { ...observation().benchmark, outcome: "validation_failure" },
      })}
    />,
  );

  const unavailable = screen.getByRole("region", { name: "Unavailable prediction" });
  expect(unavailable).toHaveTextContent("Prediction unavailable");
  expect(unavailable).toHaveTextContent("Candidate source quote failed validation.");
  expect(screen.getByText("Expected relationships")).toBeTruthy();
  expect(screen.getAllByText("Expected").length).toBeGreaterThan(0);
  expect(screen.queryByRole("region", { name: "Predicted graph" })).toBeNull();
  fireEvent.click(within(screen.getByRole("region", { name: "Expected graph" }))
    .getByRole("button", { name: /parent_of · expected/ }));
  expect(screen.getByText("Evidence for Ada · parent_of · Bela")).toBeTruthy();
});

it("restores a controlled relationship selection and preserves a predicted graph trigger for Return", () => {
  const onSelectedEdgeChange = vi.fn();
  const { rerender } = render(
    <ConditionInspection
      runId="run-1"
      observation={observation()}
      selectedEdgeKey={null}
      onSelectedEdgeChange={onSelectedEdgeChange}
    />,
  );
  const predictedGraph = screen.getByRole("region", { name: "Predicted graph" });
  fireEvent.click(within(predictedGraph).getByRole("button", { name: /spouse_of · unsupported/ }));
  expect(onSelectedEdgeChange).toHaveBeenCalledWith(JSON.stringify(["Ada", "spouse_of", "Cam"]));

  rerender(
    <ConditionInspection
      runId="run-1"
      observation={observation()}
      selectedEdgeKey={JSON.stringify(["Ada", "spouse_of", "Cam"])}
      onSelectedEdgeChange={onSelectedEdgeChange}
    />,
  );
  expect(screen.getByText("Evidence for Ada · spouse_of · Cam")).toBeTruthy();
});
