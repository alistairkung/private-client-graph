import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Usage } from "./Usage";
import type { PublicResearchSnapshot } from "./types";
const snapshot: PublicResearchSnapshot = JSON.parse(
  readFileSync(
    resolve(
      import.meta.dirname,
      "../../../../private_client_graph/published/research-results.v1.json",
    ),
    "utf8",
  ),
);
it("distinguishes the zero-call control from unpriced recorded provider calls without exposing communications", () => {
  render(<Usage runs={snapshot.runs} />);
  fireEvent.click(screen.getByText("Run A′: 0 provider calls"));
  expect(
    screen.getByText(
      "Zero provider calls. This control used deterministic replay.",
    ),
  ).toBeVisible();
  fireEvent.click(screen.getByText("Run B: 10 provider calls"));
  fireEvent.click(screen.getAllByText(/heldout_03 · Resolution/)[0]);
  expect(screen.getAllByText("Unpriced").length).toBeGreaterThan(0);
  expect(
    screen.queryByText(/system prompt|authorization|raw response/i),
  ).not.toBeInTheDocument();
});
