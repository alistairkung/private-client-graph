import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { PublicHeader } from "./PublicHeader";

test("public results navigation returns to the landing approach and demonstration", () => {
  window.history.replaceState({}, "", "/research-results");
  render(<PublicHeader />);
  expect(screen.getByRole("link", { name: "The approach" })).toHaveAttribute("href", "/#approach");
  expect(screen.getByRole("link", { name: "Explore cases" })).toHaveAttribute("href", "/#case-01");
  expect(screen.getByRole("link", { name: "Research results" })).toHaveAttribute("aria-current", "page");
  window.history.replaceState({}, "", "/");
});
