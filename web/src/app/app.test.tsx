import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { App } from "./App";

test.each(["/app", "/app/"])(
  "%s composes the practitioner shell without requesting showcase data",
  async (path) => {
    window.history.replaceState(null, "", path);
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify([])));

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
    expect(fetcher).toHaveBeenCalledOnce();
    expect(fetcher.mock.calls[0][0]).toBe("/api/matters");
    expect(document.title).toBe("Matters · Private Client Graph");
  },
);

test("practitioner notice and logout protect the synthetic session", async () => {
  window.history.replaceState(null, "", "/app");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify([])));
  render(<App />);
  expect(screen.getByText(/not suitable for real confidential client information/i)).toBeVisible();
  expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
});
