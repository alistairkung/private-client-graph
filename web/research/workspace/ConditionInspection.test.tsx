import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { CanonicalState, RunObservation } from "../shared/contracts";
import { ConditionInspection } from "./ConditionInspection";

vi.mock("../../src/features/review/GraphDrawing", () => ({
  GraphDrawing: ({
    state,
    outcomes,
    onSelect,
  }: {
    state: CanonicalState;
    outcomes?: Array<string | undefined>;
    onSelect: (index: number, trigger?: HTMLButtonElement) => void;
  }) => (
    <div aria-label="Drawn entities">
      {state.entities.map(({ id, name }) => <span key={id}>{name}</span>)}
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
    <section aria-label="Selected relationship evidence">Evidence for {edge.join(" · ")}</section>
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
    ...predicted,
    relationships: [],
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
    .getByText("Graph constructed · 0 relationships")).toBeTruthy();
  expect(within(screen.getByRole("group", { name: "Relationship outcomes" }))
    .getByText(/Missing/)).toBeTruthy();
  expect(screen.queryByText("Prediction unavailable")).toBeNull();
  fireEvent.click(screen.getByText("Graph options"));
  fireEvent.click(screen.getByRole("checkbox", { name: /Show isolated entities/ }));
  expect(within(screen.getByRole("region", { name: "Predicted graph" }))
    .getByLabelText("Drawn entities")).toHaveTextContent("Cam");
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
  expect(screen.getByRole("button", { name: /Expected relationships/ })).toBeVisible();
  expect(screen.getAllByText("Expected").length).toBeGreaterThan(0);
  expect(screen.queryByRole("region", { name: "Predicted graph" })).toBeNull();
  fireEvent.click(within(screen.getByRole("region", { name: "Expected graph" }))
    .getByRole("button", { name: /parent_of · expected/ }));
  expect(screen.getByText("Evidence for Ada · parent_of · Bela")).toBeTruthy();
});

it("restores a controlled relationship selection in the inspector", () => {
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


it("keeps each side's isolated entities in the roster and out of its drawing until shown", () => {
  const isolatedOnExpected = {
    ...expected,
    relationships: [expected.relationships[0]],
  };
  render(<ConditionInspection runId="run-1" observation={observation({
    benchmark: { ...observation().benchmark, expected: isolatedOnExpected },
    relationships: observation().relationships.filter(({ outcome }) => outcome !== "missing"),
  })} />);

  const expectedGraph = within(screen.getByRole("region", { name: "Expected graph" }));
  const predictedGraph = within(screen.getByRole("region", { name: "Predicted graph" }));
  fireEvent.click(screen.getByText("Graph options"));
  const toggle = screen.getByRole("checkbox", { name: /Show isolated entities/ });
  expect(toggle).not.toBeChecked();
  expect(toggle.parentElement).toHaveTextContent("Expected 1 · Predicted 0");
  expect(expectedGraph.getByLabelText("Drawn entities")).not.toHaveTextContent("Cam");
  expect(predictedGraph.getByLabelText("Drawn entities")).toHaveTextContent("Cam");
  fireEvent.click(screen.getByText(/Expected Matter roster/));
  expect(screen.getByRole("list", { name: "Expected entities" })).toHaveTextContent("Cam");

  fireEvent.click(toggle);
  expect(expectedGraph.getByLabelText("Drawn entities")).toHaveTextContent("Cam");

  fireEvent.click(expectedGraph.getByRole("button", { name: /parent_of · correct/ }));
  expect(screen.getByText("Evidence for Ada · parent_of · Bela")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Graphs" }));
  expect(expectedGraph.getByLabelText("Drawn entities")).toHaveTextContent("Cam");

  fireEvent.click(screen.getByText("Graph options"));
  fireEvent.click(screen.getByRole("checkbox", { name: /Show isolated entities/ }));
  expect(expectedGraph.getByLabelText("Drawn entities")).not.toHaveTextContent("Cam");
  expect(isolatedOnExpected.entities).toHaveLength(3);
});


it("opens the relationship inspector with the selected outcome filter", () => {
  render(<ConditionInspection runId="run-1" observation={observation()} />);
  const outcomes = screen.getByRole("group", { name: "Relationship outcomes" });
  fireEvent.click(within(outcomes).getByRole("button", { name: "Missing 1" }));
  const list = screen.getByRole("region", { name: "Relationship list" });
  expect(within(list).getByRole("heading", { name: "Missing relationships" })).toBeVisible();
  expect(within(list).getByRole("button", { name: /Bela spouse of Cam Missing/ })).toBeVisible();
  expect(within(list).queryByRole("button", { name: /Ada parent of Bela/ })).toBeNull();
  expect(screen.queryByRole("region", { name: "Expected graph" })).toBeNull();
});
