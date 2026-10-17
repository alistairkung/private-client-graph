import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EvidenceInspector, sourceSegments } from "./EvidenceInspector";
import type { EvidenceQuote, RelationshipOutcome } from "../shared/contracts";

const quote: EvidenceQuote = {
  id: "evidence-1",
  source_id: "source-hash",
  text: "Beth",
  occurrences: [
    [2, 6],
    [11, 15],
  ],
};
it("uses Unicode code points and highlights every recorded occurrence without losing Source text", () => {
  const source = "😀 Beth and Beth";
  const parts = sourceSegments(source, quote);
  expect(parts.map((part) => part.text).join("")).toBe(source);
  expect(
    parts.filter((part) => part.highlighted).map((part) => part.text),
  ).toEqual(["Beth", "Beth"]);
});
it("keeps missing predictions separate and focuses exact Source after selection", async () => {
  const row: RelationshipOutcome = {
    id: "rel",
    edge: ["Beth", "spouse_of", "John"],
    outcome: "missing",
    expected: [quote],
    predicted: [],
  };
  Element.prototype.scrollIntoView = vi.fn();
  render(<EvidenceInspector relationship={row} source="😀 Beth and Beth" />);
  expect(screen.getByText("No predicted relationship")).toBeVisible();
  expect(
    screen.queryByRole("button", { name: "View predicted in Source" }),
  ).not.toBeInTheDocument();
  await userEvent.click(
    screen.getByRole("button", { name: "View expected in Source" }),
  );
  const source = screen.getByRole("article", { name: "Frozen Source" });
  expect(source).toHaveFocus();
  expect(source.querySelectorAll("mark")).toHaveLength(2);
  expect(screen.getByText(/no authoritative occurrence/)).toBeVisible();
});

it("uses explicit Source identity when titles and quotes repeat", async () => {
  const row: RelationshipOutcome = {
    id: "sourced-rel",
    edge: ["Beth", "spouse_of", "John"],
    outcome: "matched",
    expected: [],
    predicted: [{ ...quote, source_id: "second", occurrences: [[7, 11]] }],
  };
  Element.prototype.scrollIntoView = vi.fn();
  render(
    <EvidenceInspector
      relationship={row}
      source="legacy combined view must not be used"
      sources={[
        { id: "first", title: "Note", text: "First Beth" },
        { id: "second", title: "Note", text: "Second Beth" },
      ]}
    />,
  );
  await userEvent.click(screen.getByRole("button", { name: "View predicted in Source" }));
  const article = screen.getByRole("article", { name: "Frozen Source" });
  expect(article.textContent).toBe("Second Beth");
  expect(article.querySelector("mark")?.textContent).toBe("Beth");
  expect(screen.getByText("Frozen Source · Note (second)")).toBeVisible();
});
