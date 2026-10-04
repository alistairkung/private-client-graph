import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { ReviewWorkspace } from "./ReviewWorkspace";
import type { CanonicalGraph } from "../../shared/canonical-graph";

// Replace canvas rendering only; selection and evidence behavior remain real.
vi.mock("./GraphView", () => ({
  GraphView: ({ onSelect }: { onSelect: (index: number) => void }) => (
    <button onClick={() => onSelect(0)}>Select spouse relationship</button>
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
    screen.getByRole("button", { name: "Select spouse relationship" }),
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
    screen.getByRole("button", { name: "Select spouse relationship" }),
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
    name: "Select spouse relationship",
  });
  await user.click(edge);
  const scrolls = vi.mocked(HTMLElement.prototype.scrollIntoView).mock.calls
    .length;
  await user.click(edge);
  expect(HTMLElement.prototype.scrollIntoView).toHaveBeenCalledTimes(
    scrolls + 1,
  );
});

test("legend explains entity shapes and both relationship directions", () => {
  render(<ReviewWorkspace source={source} graph={graph} />);
  const legend = screen.getByLabelText("Graph legend");
  expect(legend).toHaveTextContent("Person");
  expect(legend).toHaveTextContent("Trust");
  expect(legend).toHaveTextContent("Arrow points to target");
  expect(legend).toHaveTextContent("Symmetric relationship");
});
