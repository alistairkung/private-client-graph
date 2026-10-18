import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { ResearchAccordion } from "./ResearchAccordion";

vi.stubGlobal("scrollTo", vi.fn());

const preference = vi.hoisted(() => ({ reduced: false }));
vi.mock("motion/react", async original => ({
  ...await original<typeof import("motion/react")>(),
  useReducedMotion: () => preference.reduced,
}));

it("supports keyboard navigation and independently keeps multiple panels expanded", async () => {
  preference.reduced = true;
  const user = userEvent.setup();
  render(<ResearchAccordion items={[
    { id: "replay", title: "Replay calls", content: <p>Zero provider calls</p> },
    { id: "resolver", title: "Resolver calls", content: <p>Ten resolution calls</p> },
  ]} />);
  const replay = screen.getByRole("button", { name: "Replay calls" });
  const resolver = screen.getByRole("button", { name: "Resolver calls" });
  replay.focus();
  await user.keyboard("{Enter}{Tab}");
  expect(resolver).toHaveFocus();
  await user.keyboard(" ");
  expect(replay).toHaveAttribute("aria-expanded", "true");
  expect(resolver).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByText("Zero provider calls")).toBeVisible();
  expect(screen.getByText("Ten resolution calls")).toBeVisible();
});

it("isolates nested disclosures and keeps labelled panel identities stable across reversal", async () => {
  preference.reduced = true;
  render(<ResearchAccordion items={[{ id: "run", title: "Run B", content:
    <ResearchAccordion items={[{ id: "call", title: "Call 03", content: <p>Recorded tokens</p> }]} />,
  }]} />);
  const run = screen.getByRole("button", { name: "Run B" });
  const id = run.getAttribute("aria-controls");
  fireEvent.click(run);
  fireEvent.click(screen.getByRole("button", { name: "Call 03" }));
  expect(within(screen.getByRole("region", { name: "Call 03" })).getByText("Recorded tokens")).toBeVisible();
  expect(run).toHaveAttribute("aria-expanded", "true");
  fireEvent.click(run);
  fireEvent.click(run);
  expect(run).toHaveAttribute("aria-controls", id);
  expect(run).toHaveAttribute("aria-expanded", "true");
});

it("makes exiting content inert immediately while its visual collapse finishes", async () => {
  preference.reduced = false;
  render(<ResearchAccordion items={[{ id: "record", title: "Recorded data", content: <button>Inspect record</button> }]} />);
  const trigger = screen.getByRole("button", { name: "Recorded data" });
  fireEvent.click(trigger);
  await waitFor(() => expect(screen.getByRole("button", { name: "Inspect record" })).toBeVisible());
  fireEvent.click(trigger);
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  expect(screen.getByText("Inspect record").closest("[inert]")).not.toBeNull();
  expect(screen.queryByRole("button", { name: "Inspect record" })).not.toBeInTheDocument();
});
