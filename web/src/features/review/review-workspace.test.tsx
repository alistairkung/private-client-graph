import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { ReviewWorkspace } from "./ReviewWorkspace";
import type { CanonicalGraph } from "../../shared/canonical-graph";

// Replace canvas rendering only; selection and evidence behavior remain real.
vi.mock("./GraphView", () => ({
  GraphView: ({ graph, onSelect }: { graph: CanonicalGraph; onSelect: (index: number) => void }) => (
    <>{graph.relationships.map((_, index) =>
      <button key={index} onClick={() => onSelect(index)}>Select relationship {index}</button>)}</>
  ),
}));
const graph: CanonicalGraph = {
  entities: [
    { id: "a", name: "Alice", type: "person" },
    { id: "b", name: "Bob", type: "person" },
  ],
  relationships: [
    { source: "a", target: "b", type: "spouse_of", evidence_ids: ["e1", "e2"] },
  ],
  evidence: [
    {
      id: "e1",
      document: "source.txt",
      supporting_text: "Alice and Bob are spouses.",
    },
    {
      id: "e2",
      document: "source.txt",
      supporting_text: "They confirmed their marriage.",
    },
  ],
};
const source =
  "Introduction. Alice and Bob are spouses. Later. They confirmed their marriage. End.";

test("edge selection activates first evidence and changing evidence moves the single exact highlight", async () => {
  const user = userEvent.setup();
  const { container } = render(
    <ReviewWorkspace source={source} graph={graph} />,
  );
  expect(container.querySelector("mark")).toBeNull();
  await user.click(
    screen.getByRole("button", { name: "Select relationship 0" }),
  );
  expect(container.querySelectorAll("mark")).toHaveLength(1);
  expect(container.querySelector("mark")?.textContent).toBe(
    "Alice and Bob are spouses.",
  );
  expect(screen.getAllByRole("button", { name: /Evidence \d/ })).toHaveLength(
    2,
  );
  await user.click(screen.getByRole("button", { name: /Evidence 2/ }));
  expect(container.querySelectorAll("mark")).toHaveLength(1);
  expect(container.querySelector("mark")?.textContent).toBe(
    "They confirmed their marriage.",
  );
  expect(HTMLElement.prototype.scrollIntoView).toHaveBeenCalled();
  expect(screen.getByLabelText("Source document").textContent).toBe(source);
});

test("missing canonical evidence is an explicit client contract error", async () => {
  const user = userEvent.setup();
  const { container } = render(
    <ReviewWorkspace source="Unrelated source" graph={graph} />,
  );
  await user.click(
    screen.getByRole("button", { name: "Select relationship 0" }),
  );
  expect(screen.getByRole("alert")).toHaveTextContent(
    "could not be located in the source",
  );
  expect(container.querySelector("mark")).toBeNull();
});

test("selecting an edge again returns to its evidence even when the quote is unchanged", async () => {
  const user = userEvent.setup();
  render(<ReviewWorkspace source={source} graph={graph} />);
  const edge = screen.getByRole("button", {
    name: "Select relationship 0",
  });
  await user.click(edge);
  const scrolls = vi.mocked(HTMLElement.prototype.scrollIntoView).mock.calls
    .length;
  await user.click(edge);
  expect(HTMLElement.prototype.scrollIntoView).toHaveBeenCalledTimes(
    scrolls + 1,
  );
});

test("legend distinguishes Trust roles from directional and symmetric family relationships", () => {
  render(<ReviewWorkspace source={source} graph={graph} />);
  const legend = screen.getByLabelText("Graph legend");
  expect(legend).toHaveTextContent("Person");
  expect(legend).toHaveTextContent("Trust");
  expect(legend).toHaveTextContent("Trust role · no flow implied");
  expect(legend).toHaveTextContent("Parent → child");
  expect(legend).toHaveTextContent("Spouse / sibling");
});


test("relationships sharing endpoints select their own Evidence without merging roles", async () => {
  const user = userEvent.setup();
  const roles: CanonicalGraph = {
    entities: [
      { id: "a", name: "Alice", type: "person" },
      { id: "t", name: "Trust", type: "trust" },
    ],
    relationships: [
      { source: "a", target: "t", type: "settlor_of", evidence_ids: ["settlor"] },
      { source: "a", target: "t", type: "beneficiary_of", evidence_ids: ["beneficiary"] },
    ],
    evidence: [
      { id: "settlor", document: "source", supporting_text: "Alice settled the Trust." },
      { id: "beneficiary", document: "source", supporting_text: "Alice is also a beneficiary." },
    ],
  };
  const { container } = render(<ReviewWorkspace graph={roles}
    source="Alice settled the Trust. Alice is also a beneficiary." />);
  await user.click(screen.getByRole("button", { name: "Select relationship 0" }));
  expect(container.querySelector("mark")).toHaveTextContent("Alice settled the Trust.");
  await user.click(screen.getByRole("button", { name: "Select relationship 1" }));
  expect(container.querySelectorAll("mark")).toHaveLength(1);
  expect(container.querySelector("mark")).toHaveTextContent("Alice is also a beneficiary.");
  expect(screen.getAllByRole("button", { name: /Evidence \d/ })).toHaveLength(1);
});
