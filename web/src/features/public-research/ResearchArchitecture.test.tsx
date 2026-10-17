import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ResearchArchitecture } from "./ResearchArchitecture";

it("explores frozen stages and resolver configurations without execution controls", () => {
  render(<ResearchArchitecture runs={[]} />);
  expect(screen.queryByRole("button", { name: /Resolve aliases/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Resolver configuration" }));
  const stage = screen.getByRole("button", { name: /Resolve aliases/ });
  fireEvent.click(stage);
  expect(stage).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("region", { name: "Resolve aliases" })).toHaveTextContent("does not rewrite");
  expect(screen.queryByRole("button", { name: /Run|Execute|Authorize|Add/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Baseline configuration" }));
  expect(screen.queryByRole("button", { name: /Resolve aliases/ })).not.toBeInTheDocument();
});
