import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type { RunDetail } from "../shared/contracts";
import { ObservationInspection } from "./ObservationInspection";

it("keeps observations collapsed until explicitly expanded", () => {
  render(
    <ObservationInspection
      run={{ observations: [] } as unknown as RunDetail}
    />,
  );
  const summary = screen.getByText("Observations & Evidence");
  const observation = screen.getByLabelText("Observation");
  expect(observation).not.toBeVisible();
  fireEvent.click(summary);
  expect(observation).toBeVisible();
  fireEvent.click(summary);
  expect(observation).not.toBeVisible();
});

it("shows a rejected Source association alongside a perfect quotation score", () => {
  const result = {
    evaluation: { precision: 1, recall: 1, f1: 1, provenance_accuracy: 1 },
    source_attribution: {
      assessed: 1, passed: 0,
      failures: [{ edge: ["Jo", "trustee_of", "Elm"], evidence_id: "e1",
        source_id: "draft", supporting_text: "Jo is trustee of Elm." }],
    },
  };
  render(<ObservationInspection run={{ observations: [
    { id: "one", case_id: "test", result, relationships: [] },
  ] } as unknown as RunDetail} />);
  fireEvent.click(screen.getByText("Observations & Evidence"));
  expect(screen.getByText(/Approved Source.quote associations/)).toHaveTextContent("0 / 1");
  expect(screen.getByRole("list", { name: "Unapproved Source/quote associations" }))
    .toHaveTextContent("Jo · trustee_of · Elm — draft: Jo is trustee of Elm.");
});
