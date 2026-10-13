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
