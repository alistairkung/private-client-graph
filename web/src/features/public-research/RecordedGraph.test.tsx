import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { CanonicalGraph } from "../../shared/canonical-graph";
import { RecordedGraph, recordedGraph } from "./RecordedGraph";
import type { PublicResearchSnapshot } from "./types";

vi.mock("./recorded-review/GraphView", () => ({
  GraphView: ({ graph, selected, onSelect }: { graph: CanonicalGraph; selected: number | null; onSelect: (index: number) => void }) =>
    <>{graph.relationships.map((edge, index) => (
      <button key={index} aria-pressed={selected === index} onClick={() => onSelect(index)}>
        {graph.entities.find(entity => entity.id === edge.source)?.name}
        {index > 0 ? ` · ${edge.type}` : ""}
      </button>
    ))}</>,
}));
const snapshot: PublicResearchSnapshot = JSON.parse(readFileSync(resolve(
  import.meta.dirname, "../../../../private_client_graph/published/research-results.v1.json",
), "utf8"));
const sample = snapshot.cases.find(item => item.case_id === "heldout_03")!;

it("adapts saved state without changing graph identities, relationship ordering or Evidence", () => {
  const observation = sample.observations[0];
  const graph = recordedGraph(observation);
  expect(graph.entities).toEqual(observation.state.entities);
  expect(graph.relationships).toEqual(observation.state.relationships);
  expect(graph.evidence).toBe(observation.state.evidence);
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
