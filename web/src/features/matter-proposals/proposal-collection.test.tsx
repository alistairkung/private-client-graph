import { render, screen, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "../../app/App";

const proposal = { id: "proposal-42", external_reference: "Firm/42", matter_title: "Fictional family" };

test("entry separates proposals awaiting confirmation from accepted Matters", async () => {
  window.history.replaceState(null, "", "/app");
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(async url => new Response(JSON.stringify(
    url === "/api/matter-proposals" ? [proposal] : [{ id: "matter-1", external_reference: "Firm/1", title: "Accepted Matter" }],
  )));
  render(<App />);
  const pending = await screen.findByRole("region", { name: "Awaiting confirmation" });
  expect(await within(pending).findByRole("link", { name: "Firm/42 Fictional family" })).toHaveAttribute("href", "/app/matter-proposals/proposal-42");
  expect(within(screen.getByRole("table", { name: "Matters" })).queryByText("Fictional family")).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Create Matter" })).toHaveAttribute("href", "/app/matter-proposals/new");
  expect(fetcher.mock.calls.map(call => call[0]).sort()).toEqual(["/api/matter-proposals", "/api/matters"]);
});
