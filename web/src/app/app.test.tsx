import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";

test.each(["/app", "/app/"])(
  "%s composes the practitioner shell without requesting showcase data",
  async (path) => {
    window.history.replaceState(null, "", path);
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => new Response(JSON.stringify([])));

    render(<App />);

    expect(screen.getByRole("heading", { name: "Matters" })).toBeVisible();
    expect(await screen.findByText("No Matters available")).toBeVisible();
    expect(screen.getByRole("link", { name: "Matters" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Public showcase" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
    expect(fetcher.mock.calls.map(call => call[0]).sort()).toEqual(["/api/matter-proposals", "/api/matters"]);
    expect(document.title).toBe("Matters · Private Client Graph");
  },
);

test("practitioner notice and logout protect the synthetic session", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response(JSON.stringify([])));
  render(<App />);
  expect(screen.getByText(/not suitable for real confidential client information/i)).toBeVisible();
  expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
});

test("creation direct entry stays in the practitioner shell and does not load analysis", () => {
  window.history.replaceState(null, "", "/app/matter-proposals/new");
  const fetcher = vi.spyOn(globalThis, "fetch");
  render(<App />);
  expect(screen.getByRole("heading", { name: "Create Matter" })).toBeVisible();
  expect(screen.getByRole("checkbox", { name: /synthetic or fictional/ })).toBeVisible();
  expect(fetcher).not.toHaveBeenCalled();
  expect(document.title).toBe("Create Matter · Private Client Graph");
});

test("proposal direct entry reads its persisted source and graph without reanalysis", async () => {
  window.history.replaceState(null, "", "/app/matter-proposals/proposal-42");
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    id: "proposal-42", external_reference: "Firm/42", matter_title: "Saved proposal",
    authoritative_source: { title: "Source title", text: "Saved source" },
    proposed_graph: { entities: [], relationships: [], evidence: [] },
  })));
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Saved proposal" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "Proposed relationships" })).toBeVisible();
  expect(fetcher).toHaveBeenCalledOnce();
  expect(fetcher.mock.calls[0][0]).toBe("/api/matter-proposals/proposal-42");
  expect(document.title).toBe("Saved proposal · Private Client Graph");
});
