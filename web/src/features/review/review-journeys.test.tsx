import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

const graph: CanonicalGraph = {
  entities: [{ id: "trust", name: "Evergreen Trust", type: "trust" }],
  relationships: [],
  evidence: [],
};

function response(body: unknown) {
  return new Response(JSON.stringify(body));
}

test("showcase analysis and Matter detail pass their Canonical Graph to the shared review", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response({
      live_analysis: { state: "available", resets_at: null },
      title: "Case 01",
      notice: "Synthetic case",
      source_text: "Shared source",
    }))
    .mockResolvedValueOnce(response({
      execution: { mode: "sample", run_artifact_id: null },
      graph,
    }));
  const user = userEvent.setup();
  const showcase = render(<ShowcaseApp />);

  await screen.findByText("Shared source");
  await user.click(screen.getByRole("button", { name: "Load sample analysis" }));
  await screen.findByText("Shared relationship review");
  const showcaseGraph = reviewWorkspaceProps.mock.lastCall?.[0].graph;

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
  expect(showcaseGraph).toEqual(graph);
  expect(matterGraph).toEqual(graph);
});
