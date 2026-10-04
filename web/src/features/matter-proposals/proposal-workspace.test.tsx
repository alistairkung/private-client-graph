import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { ProposalWorkspace } from "./ProposalWorkspace";

const proposal = {
  id: "proposal-42", external_reference: "Firm/42", matter_title: "Fictional family",
  authoritative_source: { title: "Attendance note", text: "A synthetic source without supported relationships." },
  proposed_graph: { entities: [], relationships: [], evidence: [] },
};

test("empty proposed graph remains reviewable and discard requires a separate destructive confirmation", async () => {
  const fetcher = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response(JSON.stringify(proposal)))
    .mockResolvedValueOnce(new Response(null, { status: 204 }));
  const navigate = vi.fn();
  render(<ProposalWorkspace id="proposal-42" onNavigate={navigate} />);
  expect(await screen.findByRole("heading", { name: "Fictional family" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "Proposed relationships" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "No supported relationships proposed" })).toBeVisible();
  expect(screen.getByLabelText("Source document")).toHaveTextContent(proposal.authoritative_source.text);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Discard intake" }));
  expect(fetcher).toHaveBeenCalledOnce();
  expect(screen.getByRole("region", { name: "Discard this intake?" })).toHaveTextContent("permanently removes");
  await user.click(screen.getByRole("button", { name: "Keep intake" }));
  expect(screen.queryByRole("button", { name: "Permanently discard intake" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Discard intake" }));
  await user.click(screen.getByRole("button", { name: "Permanently discard intake" }));
  expect(navigate).toHaveBeenCalledWith("/app");
  expect(fetcher.mock.calls[1][0]).toBe("/api/matter-proposals/proposal-42");
  expect(fetcher.mock.calls[1][1]?.method).toBe("DELETE");
});

test("a lost discard response preserves review and directs the practitioner to check the collections", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(new Response(JSON.stringify(proposal)))
    .mockRejectedValueOnce(new TypeError("Connection lost"));
  const navigate = vi.fn();
  render(<ProposalWorkspace id="proposal-42" onNavigate={navigate} />);
  await screen.findByRole("heading", { name: "Fictional family" });
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Discard intake" }));
  await user.click(screen.getByRole("button", { name: "Permanently discard intake" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Discard could not be confirmed");
  expect(screen.getByRole("link", { name: "Check Matters and proposals" })).toHaveAttribute("href", "/app");
  expect(navigate).not.toHaveBeenCalled();
  expect(screen.getByLabelText("Source document")).toBeVisible();
});

test.each([404, 503])("proposal detail %s offers return without stale or fallback data", async status => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status }));
  render(<ProposalWorkspace id="unavailable" onNavigate={vi.fn()} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(status === 404 ? "Matter Proposal not found" : "Matter Proposal could not be loaded.");
  expect(screen.getByRole("link", { name: "Back to Matters" })).toHaveAttribute("href", "/app");
  expect(screen.queryByLabelText("Source document")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Discard intake" })).not.toBeInTheDocument();
});
