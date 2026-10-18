import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { PublicHeader } from "./PublicHeader";

test("public results navigation returns to the landing approach and demonstration", () => {
  window.history.replaceState({}, "", "/research-results");
  render(<PublicHeader />);
  expect(screen.getByRole("link", { name: "The approach" })).toHaveAttribute("href", "/#landing-main");
  expect(screen.getByRole("link", { name: "Explore cases" })).toHaveAttribute("href", "/app?example=case-01");
  expect(screen.getByRole("link", { name: "Research results" })).toHaveAttribute("aria-current", "page");
  window.history.replaceState({}, "", "/");
});

test("compact navigation opens, closes with Escape and dismisses outside with language controls inside the menu", () => {
  vi.stubGlobal("matchMedia", () => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  try {
    render(<PublicHeader />);
    const menu = screen.getByRole("button", { name: "Menu" });
    expect(screen.queryByRole("link", { name: "The approach" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "简体中文" })).not.toBeInTheDocument();
    fireEvent.click(menu);
    expect(screen.getByRole("button", { name: "简体中文" })).toBeVisible();
    expect(screen.getByRole("link", { name: "The approach" })).toBeVisible();
    fireEvent.keyDown(menu, { key: "Escape" });
    expect(menu).toHaveFocus();
    expect(menu).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(menu);
    fireEvent.pointerDown(document.body);
    expect(menu).toHaveAttribute("aria-expanded", "false");
  } finally { vi.unstubAllGlobals(); }
});
