import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { CanonicalState } from "../../shared/contracts";
import { GraphDrawing } from "../review/GraphDrawing";
import { RecordedGraph } from "./RecordedGraph";
import type { PublicResearchSnapshot } from "./types";

vi.mock("../review/GraphDrawing", () => ({
  GraphDrawing: vi.fn(({ state: graph, selected, onSelect, onEntity }: { state: CanonicalState; selected: number | null; onSelect: (index: number) => void; onEntity: (id: string) => void }) =>
    <>{graph.entities.map(entity => <button key={entity.id} onClick={() => onEntity(entity.id)}>Select entity {entity.name}</button>)}
    {graph.relationships.map((edge, index) => (
      <button key={index} aria-pressed={selected === index} onClick={() => onSelect(index)}>
        {graph.entities.find(entity => entity.id === edge.source)?.name}
        {index > 0 ? ` · ${edge.type}` : ""}
      </button>
    ))}</>),
}));
const snapshot: PublicResearchSnapshot = JSON.parse(readFileSync(resolve(
  import.meta.dirname, "../../../../private_client_graph/published/research-results.v1.json",
), "utf8"));
const sample = snapshot.cases.find(item => item.case_id === "heldout_03")!;

it("passes the complete retained canonical state directly to the actual Matter graph renderer", () => {
  render(<RecordedGraph sample={sample} />);
  expect(vi.mocked(GraphDrawing).mock.calls.at(-1)?.[0].state).toBe(sample.observations[0].state);
});
it("joins a selected graph edge to its recorded outcome and unchanged quote across conditions", () => {
  render(<RecordedGraph sample={sample} />);
  fireEvent.click(screen.getByRole("button", { name: "Bea" }));
  expect(screen.getByText("Bea · parent_of · Isaac Ng")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "View predicted in Source" }));
  const source = screen.getByRole("article", { name: "Frozen Source" });
  expect(source.querySelector("mark")).toHaveTextContent("Bea is the parent of Isaac Ng.");
  const quote = source.querySelector("mark")!.textContent;
  fireEvent.click(screen.getByRole("button", { name: "Resolved relationships · B" }));
  expect(screen.queryByRole("article")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Beatrice Ng" }));
  expect(screen.getByText("Beatrice Ng · parent_of · Isaac Ng")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "View predicted in Source" }));
  expect(screen.getByRole("article").querySelector("mark")).toHaveTextContent(quote!);
});

it("preserves an unchanged relationship selection when its position differs between recorded runs", () => {
  const reordered = structuredClone(sample);
  const resolved = reordered.observations.find(item => item.run_label === "B")!;
  resolved.state.relationships.reverse();
  render(<RecordedGraph sample={reordered} />);
  fireEvent.click(screen.getByRole("button", { name: "Isaac Ng · beneficiary_of" }));
  expect(screen.getByText("Isaac Ng · beneficiary_of · Larch Family Trust")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "View predicted in Source" }));
  const source = screen.getByRole("article", { name: "Frozen Source" });
  fireEvent.click(screen.getByRole("button", { name: "Resolved relationships · B" }));
  expect(screen.getByText("Isaac Ng · beneficiary_of · Larch Family Trust")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Isaac Ng" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("article", { name: "Frozen Source" })).toBe(source);
});

it("preserves inspected Source evidence when the selected condition is clicked again", () => {
  render(<RecordedGraph sample={sample} />);
  fireEvent.click(screen.getByRole("button", { name: "Bea" }));
  fireEvent.click(screen.getByRole("button", { name: "View predicted in Source" }));
  fireEvent.click(screen.getByRole("button", { name: "Original extraction · A" }));
  expect(screen.getByRole("article", { name: "Frozen Source" }).querySelector("mark"))
    .toHaveTextContent("Bea is the parent of Isaac Ng.");
});

it("shows incident relationships for an entity and clears stale Evidence until an edge is selected", () => {
  render(<RecordedGraph sample={sample} />);
  fireEvent.click(screen.getByRole("button", { name: "Bea" }));
  fireEvent.click(screen.getByRole("button", { name: "View predicted in Source" }));
  fireEvent.click(screen.getByRole("button", { name: "Select entity Bea" }));
  expect(screen.queryByRole("article")).not.toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: "Entity relationships" })).toHaveTextContent("Bea");
  fireEvent.click(screen.getByRole("button", { name: /Bea · parent_of · Isaac Ng/ }));
  expect(screen.queryByRole("complementary", { name: "Entity relationships" })).not.toBeInTheDocument();
  expect(screen.getByText("Bea · parent_of · Isaac Ng")).toBeInTheDocument();
});

it("resets selection and the research camera identity when the case changes", () => {
  const { rerender } = render(<RecordedGraph sample={sample} />);
  fireEvent.click(screen.getByRole("button", { name: "Bea" }));
  rerender(<RecordedGraph sample={snapshot.cases[0]} />);
  expect(screen.getByText("Select a relationship in this result.")).toBeInTheDocument();
  expect(vi.mocked(GraphDrawing).mock.calls.at(-1)?.[0].memoryKey).toBe(`research:recorded:${snapshot.cases[0].case_id}`);
});
