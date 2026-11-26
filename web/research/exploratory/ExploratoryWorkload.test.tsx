import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ExploratoryWorkload } from "./ExploratoryWorkload";

afterEach(() => vi.unstubAllGlobals());

it("inspects exact Source text in delivered order", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({
    manifest: { workload_id: "example", source_file_sha256: "test-digest" },
    sources: [
      { id: "z-last-alphabetically", title: "First in custody", text: "First original body." },
      { id: "a-first-alphabetically", title: "Second in custody", text: "Second original body." },
    ],
  })));
  render(<ExploratoryWorkload />);

  const picker = await screen.findByRole("combobox", { name: "Frozen Source" });
  expect(screen.getByText("First original body.")).toBeVisible();
  expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
    "1. First in custody", "2. Second in custody",
  ]);
  fireEvent.change(picker, { target: { value: "a-first-alphabetically" } });
  expect(screen.getByText("Second original body.")).toBeVisible();
  expect(screen.queryByText("First original body.")).not.toBeInTheDocument();
});

it("retries an unavailable release without inventing Source content", async () => {
  const fetch = vi.fn()
    .mockResolvedValueOnce(new Response(null, { status: 409 }))
    .mockResolvedValueOnce(Response.json({
      manifest: { workload_id: "example", source_file_sha256: "test-digest" },
      sources: [{ id: "one", title: "Original", text: "Original body." }],
    }));
  vi.stubGlobal("fetch", fetch);
  render(<ExploratoryWorkload />);

  expect(await screen.findByRole("alert")).toHaveTextContent("could not be loaded");
  expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Retry read" }));
  expect(await screen.findByText("Original body.")).toBeVisible();
});
