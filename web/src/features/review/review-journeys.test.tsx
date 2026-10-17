import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { MatterWorkspace } from "../matters/MatterWorkspace";
import { ShowcaseApp } from "../showcase/ShowcaseApp";
import type { CanonicalGraph } from "../../shared/canonical-graph";

const reviewWorkspaceProps = vi.fn();
vi.mock("./ReviewWorkspace", () => ({
  ReviewWorkspace: (props: { graph: CanonicalGraph }) => {
    reviewWorkspaceProps(props);
    return <div>Shared relationship review</div>;
  },
}));

const sourceAwareProps = vi.fn();
vi.mock("./SourceAwareReviewWorkspace", () => ({
  SourceAwareReviewWorkspace: (props: unknown) => {
    sourceAwareProps(props);
    return <div>Shared source-aware review</div>;
  },
}));

const graph: CanonicalGraph = {
  entities: [{ id: "trust", name: "Evergreen Trust", type: "trust" }],
  relationships: [],
  evidence: [],
};

function response(body: unknown) {
  return new Response(JSON.stringify(body));
}

test("showcase passes source-aware facts and Matter detail retains its legacy graph contract", async () => {
  const state = { ...graph, sources: [{id: "note", title: "Attendance note", text: "Shared source"}] };
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response([{id: "case-01",title: "Case 01",description: "Synthetic"}]))
    .mockResolvedValueOnce(response({id: "case-01",title: "Case 01",description: "Synthetic", state}));
  const showcase = render(<ShowcaseApp />);
  await screen.findByText("Shared source-aware review");
  const showcaseState = sourceAwareProps.mock.lastCall?.[0].state;

  showcase.unmount();
  fetcher.mockResolvedValueOnce(response({
    id: "ff985caf-60c5-4e65-a238-f3c26381c369",
    external_reference: "PC/2026/0142",
    title: "Evergreen Family Trust",
    authoritative_source: { title: "Attendance note", text: "Shared source" },
    current_graph: graph,
  }));
  render(<MatterWorkspace id="ff985caf-60c5-4e65-a238-f3c26381c369" />);

  await screen.findByText("Shared relationship review");
  const matterGraph = reviewWorkspaceProps.mock.lastCall?.[0].graph;
  expect(showcaseState).toEqual(state);
  expect(matterGraph).toEqual(graph);
});
