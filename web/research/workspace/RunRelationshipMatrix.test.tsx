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

it("keeps each proof category inside the graph true-positive cell", () => {
  render(<RunRelationshipMatrix
    scope="34 qualified Conditions"
    counts={{ tp: 8, fp: 3, fn: 2 }}
    expectedEdgesWithoutGraph={0}
    proofBreakdown={{ complete: 2, incomplete: 5, withoutFormalTarget: 1 }}
  />);
  const table = within(screen.getByRole("table", {
    name: "Relationship confusion matrix · 34 qualified Conditions",
  }));
  const truePositives = within(table.getByRole("cell", { name: /8 TP.*Complete approved proof/ }));
  expect(truePositives.getByText("Complete approved proof")).toBeVisible();
  expect(truePositives.getByText("Incomplete formal proof")).toBeVisible();
  expect(truePositives.getByText("No formal proof target")).toBeVisible();
  expect(truePositives.getAllByRole("definition").map((entry) => entry.textContent)).toEqual(["2", "5", "1"]);
  expect(table.getByRole("cell", { name: /3 FP/ })).toBeVisible();
  expect(table.getByRole("cell", { name: /2 FN/ })).toBeVisible();
  expect(table.getByRole("cell", { name: /TN · Unscored/ })).toBeVisible();
});
