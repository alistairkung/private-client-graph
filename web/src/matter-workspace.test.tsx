import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";

const id = "ff985caf-60c5-4e65-a238-f3c26381c369";
test("direct Matter entry loads its persisted source and graph without analysis", async () => {
  window.history.replaceState(null, "", `/app/matters/${id}`);
  const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
    id, external_reference: "Firm/42", title: "Persisted Matter",
    authoritative_source: { title: "Persisted source title", text: "Persisted source text" },
    current_graph: { entities: [], relationships: [], evidence: [] },
  })));
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Persisted Matter" })).toBeVisible();
  expect(screen.getByText("Matter reference: Firm/42")).toBeVisible();
  expect(screen.getByLabelText("Source document")).toHaveTextContent("Persisted source text");
  expect(screen.getByRole("heading", { name: "Persisted source title" })).toBeVisible();
  expect(fetcher).toHaveBeenCalledExactlyOnceWith(`/api/matters/${id}`);
  expect(screen.queryByRole("button", { name: /analysis/i })).not.toBeInTheDocument();
  expect(document.title).toBe("Persisted Matter · Private Client Graph");
});

test.each([404, 503])("Matter %s offers a return route without fallback data", async status => {
  window.history.replaceState(null, "", `/app/matters/${id}`);
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status }));
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent(status === 404 ? "Matter not found" : "Matter could not be loaded.");
  expect(screen.getByRole("link", { name: "Back to Matters" })).toHaveAttribute("href", "/app");
  expect(screen.queryByLabelText("Source document")).not.toBeInTheDocument();
});
