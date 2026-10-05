import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import extraction from "../../../../cases/case_01/expected_extraction.json";
import type { CanonicalGraph, RelationshipType } from "../../shared/canonical-graph";
import type { CaseAnalysis } from "./types";
import { resolveSamplePassages } from "./sample-walkthrough";
import { SampleWalkthrough } from "./SampleWalkthrough";
import { ShowcaseApp } from "./ShowcaseApp";

// Mapping tests deliberately use arbitrary IDs and reversed relationship order.
// Browser coverage keeps API graph construction real.
const names = ["Alice Chen", "David Chen", "Bob Chen", "Carol Wong", "Evergreen Family Trust"];
const source = readFileSync("../cases/case_01/source.txt", "utf8");
const graph: CanonicalGraph = {
  entities: names.map((name, index) => ({ id: `entity-${index}`, name, type: index === 4 ? "trust" : "person" })),
  relationships: extraction.relationships.map((item, index) => ({
    source: `entity-${names.indexOf(item.source_name)}`, target: `entity-${names.indexOf(item.target_name)}`,
    type: item.relationship_type as RelationshipType, evidence_ids: [`quote-${index}`],
  })).reverse(),
  evidence: extraction.relationships.map((item, index) => ({
    id: `quote-${index}`, document: "source.txt", supporting_text: item.supporting_text,
  })),
};
const analysis: CaseAnalysis = { execution: { mode: "sample", run_artifact_id: null }, graph };

vi.mock("../review/GraphView", () => ({
  GraphView: ({ graph, onSelect, selected }: { graph: CanonicalGraph; onSelect: (index: number) => void; selected: number | null }) =>
    <>{graph.relationships.map((_, index) => <button key={index} aria-pressed={selected === index}
      onClick={() => onSelect(index)}>Relationship {index}</button>)}</>,
}));

beforeEach(() => {
  vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
});
afterEach(() => vi.unstubAllGlobals());

test("six scene targets resolve supplied identities and verbatim Evidence without changing the graph", () => {
  const original = structuredClone(analysis);
  const passages = resolveSamplePassages(analysis, source)!;
  expect(passages.map((passage) => passage.relationshipIndex)).toEqual([5, 4, 3, 2, 1, 0]);
  expect(passages.map((passage) => passage.evidenceId)).toEqual(extraction.relationships.map((_, index) => `quote-${index}`));
  expect(passages.map((passage) => passage.quote)).toEqual(extraction.relationships.map((item) => item.supporting_text));
  expect(analysis).toEqual(original);
});

test("guidance is unavailable for live results, missing relationships, ambiguous targets or nonmatching Evidence", () => {
  expect(resolveSamplePassages({ ...analysis, execution: { mode: "live", run_artifact_id: "run" } }, source)).toBeUndefined();
  expect(resolveSamplePassages({ ...analysis, graph: { ...graph, relationships: graph.relationships.slice(1) } }, source)).toBeUndefined();
  expect(resolveSamplePassages({ ...analysis, graph: { ...graph, relationships: graph.relationships.map(() => graph.relationships[0]) } }, source)).toBeUndefined();
  expect(resolveSamplePassages({ ...analysis, graph: { ...graph, evidence: [] } }, source)).toBeUndefined();
  expect(resolveSamplePassages(analysis, "Different source")).toBeUndefined();
});

async function scrollToPassage(index: number) {
  document.querySelectorAll<HTMLElement>("[data-passage]").forEach((element, current) => {
    vi.spyOn(element, "getBoundingClientRect").mockReturnValue({ top: current <= index ? 0 : 2000 } as DOMRect);
  });
  act(() => fireEvent.scroll(window));
  // Flush the one animation frame used to batch scroll position reads.
  await act(async () => { await new Promise(requestAnimationFrame); });
}

test.each(["relationship", "Evidence", "keyboard", "source wheel"])("%s interaction permanently stops narrative selection", async (interaction) => {
  const user = userEvent.setup();
  const { container, rerender } = render(<SampleWalkthrough analysis={analysis} source={source} expanded={false} skipRequested={false} />);
  await scrollToPassage(1);
  await waitFor(() => expect(container.querySelector("mark")).toHaveTextContent(extraction.relationships[1].supporting_text));
  if (interaction === "relationship") await user.click(screen.getByRole("button", { name: "Relationship 1" }));
  if (interaction === "Evidence") await user.click(screen.getByRole("button", { name: /Evidence 1/ }));
  if (interaction === "keyboard") fireEvent.keyDown(screen.getByRole("button", { name: "Relationship 4" }), { key: "Tab" });
  if (interaction === "source wheel") fireEvent.wheel(screen.getByRole("region", { name: "Scrollable source" }));
  const selectedQuote = container.querySelector("mark")!.textContent;
  await scrollToPassage(5);
  expect(container.querySelector("mark")!.textContent).toBe(selectedQuote);
  expect(screen.getByText(/You control the review/)).toBeVisible();
  rerender(<SampleWalkthrough analysis={analysis} source={source} expanded skipRequested={false} />);
  rerender(<SampleWalkthrough analysis={analysis} source={source} expanded={false} skipRequested={false} />);
  await scrollToPassage(0);
  expect(container.querySelector("mark")!.textContent).toBe(selectedQuote);
});

test.each(["skip", "expansion"])("%s hands off the current selection even without touching review controls", async (action) => {
  const { container, rerender } = render(<SampleWalkthrough analysis={analysis} source={source} expanded={false} skipRequested={false} />);
  await scrollToPassage(4);
  const selectedQuote = container.querySelector("mark")!.textContent;
  rerender(<SampleWalkthrough analysis={analysis} source={source} expanded={action === "expansion"} skipRequested={action === "skip"} />);
  rerender(<SampleWalkthrough analysis={analysis} source={source} expanded={false} skipRequested={false} />);
  await scrollToPassage(0);
  expect(container.querySelector("mark")!.textContent).toBe(selectedQuote);
});

test("page scrolling over the graph does not count as operating a review control", async () => {
  const { container } = render(<SampleWalkthrough analysis={analysis} source={source} expanded={false} skipRequested={false} />);
  fireEvent.wheel(screen.getByRole("button", { name: "Relationship 0" }));
  await scrollToPassage(4);
  expect(container.querySelector("mark")).toHaveTextContent(extraction.relationships[4].supporting_text);
  expect(screen.getByText(/Guided sample walkthrough\. Choose/)).toBeVisible();
});

test("mobile and reduced-motion media retain all explanations and supplied quotes without scroll selection", async () => {
  vi.mocked(window.matchMedia).mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() } as unknown as MediaQueryList);
  const { container } = render(<SampleWalkthrough analysis={analysis} source={source} expanded={false} skipRequested={false} />);
  expect(container.querySelectorAll(".sample-passage blockquote")).toHaveLength(6);
  await scrollToPassage(5);
  expect(container.querySelector("mark")).toHaveTextContent(extraction.relationships[0].supporting_text);
});

test("a differing live result remains an ordinary usable review with no sample script", async () => {
  const live: CaseAnalysis = { execution: { mode: "live", run_artifact_id: "live" }, graph: {
    ...graph, relationships: graph.relationships.slice(0, 1),
  } };
  const { container } = render(<SampleWalkthrough analysis={live} source={source} expanded={false} skipRequested={false} />);
  expect(screen.queryByLabelText("Case 01 explanation")).toBeNull();
  expect(container.querySelector("mark")).toBeNull();
  await userEvent.setup().click(screen.getByRole("button", { name: "Relationship 0" }));
  await scrollToPassage(5);
  expect(container.querySelector("mark")).toHaveTextContent(extraction.relationships[5].supporting_text);
});

test("switching analysis modes isolates the live result and starts a fresh sample review session", async () => {
  const detail = { source_text: source, title: "Case 01", notice: "Synthetic", live_analysis: { state: "available", resets_at: null } };
  const live: CaseAnalysis = { execution: { mode: "live", run_artifact_id: "live" }, graph: {
    ...graph, relationships: graph.relationships.slice(0, 1),
  } };
  const response = (body: unknown) => new Response(JSON.stringify(body));
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response(detail)).mockResolvedValueOnce(response(analysis))
    .mockResolvedValueOnce(response(live)).mockResolvedValueOnce(response(detail))
    .mockResolvedValueOnce(response(analysis));
  const user = userEvent.setup();
  const { container } = render(<ShowcaseApp />);
  await user.click(await screen.findByRole("button", { name: "Load sample analysis" }));
  await screen.findByText("Sample analysis · Demonstration fixture");
  await user.click(screen.getByRole("button", { name: "Relationship 4" }));
  await user.click(screen.getByText("Analysis options", { exact: true }));
  await user.click(screen.getByRole("button", { name: "Run live analysis" }));
  await screen.findByText("Live analysis · Newly extracted");
  expect(screen.queryByLabelText("Case 01 explanation")).toBeNull();
  expect(container.querySelector("mark")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Relationship 0" }));
  expect(container.querySelector("mark")).toHaveTextContent(extraction.relationships[5].supporting_text);
  await user.click(screen.getByRole("button", { name: "Load sample analysis" }));
  await screen.findByText("Sample analysis · Demonstration fixture");
  expect(screen.getByText(/Guided sample walkthrough\. Choose/)).toBeVisible();
});
import { readFileSync } from "node:fs";
