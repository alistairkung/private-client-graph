import { render, screen, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "../../app/App";
import { ProposalCollection } from "./ProposalCollection";

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

test.each(["http", "network"])("proposal collection %s failure never implies an empty collection", async failure => {
  const fetcher = vi.spyOn(globalThis, "fetch");
  if (failure === "http") fetcher.mockResolvedValue(new Response("Unavailable", { status: 503 }));
  else fetcher.mockRejectedValue(new TypeError("Failed to fetch"));
  render(<ProposalCollection />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Matter Proposals could not be loaded.");
  expect(screen.getByRole("alert")).toHaveTextContent("Reload the page to try again.");
  expect(screen.queryByText("No Matter Proposals awaiting confirmation")).not.toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
