import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { PractitionerApp } from "./PractitionerApp";

const matter = {
  id: "ff985caf-60c5-4e65-a238-f3c26381c369",
  external_reference: "PC/2026/0142",
  title: "Evergreen Family Trust",
};

test("loads persisted summaries and selects a Matter without leaving the ledger", async () => {
  let finish!: (value: Response) => void;
  const fetcher = vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const user = userEvent.setup();
  render(<PractitionerApp />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading Matters…");
  finish(new Response(JSON.stringify([matter])));
  const row = await screen.findByRole("button", { name: "PC/2026/0142 Evergreen Family Trust" });
  expect(row).toHaveAttribute("aria-pressed", "false");
  await user.click(row);
  expect(row).toHaveAttribute("aria-pressed", "true");
  row.focus();
  await user.keyboard("{Enter}");
  expect(row).toHaveAttribute("aria-pressed", "false");
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
