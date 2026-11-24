import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { RunRelationshipMatrix } from "./RunRelationshipMatrix";

it("labels the overall counts, unscored negatives and failed-construction contribution", () => {
  render(<RunRelationshipMatrix
    counts={{ tp: 91, fp: 10, fn: 22 }}
    expectedEdgesWithoutGraph={17}
  />);
  const table = within(screen.getByRole("table", {
    name: "Relationship confusion matrix · All conditions",
  }));
  expect(table.getByRole("cell", { name: /91 TP/ })).toBeInTheDocument();
  expect(table.getByRole("cell", { name: /22 FN/ })).toBeInTheDocument();
  expect(table.getByRole("cell", { name: /10 FP/ })).toBeInTheDocument();
  expect(table.getByRole("cell", { name: /TN · Unscored/ })).toBeInTheDocument();
  expect(screen.getByText(/17 expected relationships from conditions without a valid graph/))
    .toBeInTheDocument();
});
