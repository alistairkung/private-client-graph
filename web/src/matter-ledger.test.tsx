import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { PractitionerApp } from "./PractitionerApp";

const matter = {
  id: "ff985caf-60c5-4e65-a238-f3c26381c369",
  external_reference: "PC/2026/0142",
  title: "Evergreen Family Trust",
};

test("loads persisted summaries with a direct Matter route", async () => {
  let finish!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  render(<PractitionerApp />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading Matters…");
  finish(new Response(JSON.stringify([matter])));
  const row = await screen.findByRole("link", { name: "PC/2026/0142 Evergreen Family Trust" });
  expect(row).toHaveAttribute("href", `/app/matters/${matter.id}`);
  expect(fetcher).toHaveBeenCalledExactlyOnceWith("/api/matters");
  expect(screen.queryByText(matter.id)).not.toBeInTheDocument();
});

test.each(["http", "network"])("%s failure never displays a fallback Matter", async failure => {
  const fetcher = vi.spyOn(globalThis, "fetch");
  if (failure === "http") fetcher.mockResolvedValue(new Response("Unavailable", { status: 503 }));
  else fetcher.mockRejectedValue(new TypeError("Failed to fetch"));
  render(<PractitionerApp />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Matters could not be loaded.");
  expect(screen.getByRole("alert")).toHaveTextContent("Reload the page to try again.");
  expect(screen.queryByText("Evergreen Family Trust")).not.toBeInTheDocument();
  expect(screen.queryByText("No Matters available")).not.toBeInTheDocument();
});
