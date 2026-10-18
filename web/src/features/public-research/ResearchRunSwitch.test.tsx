import { useState } from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ResearchRunSwitch } from "./ResearchRunSwitch";
import type { RunLabel } from "./types";

const motionPreference = vi.hoisted(() => ({ reduced: false }));
vi.mock("motion/react", async importOriginal => ({
  ...await importOriginal<typeof import("motion/react")>(),
  useReducedMotion: () => motionPreference.reduced,
}));

const options = [
  { value: "A", label: "A · Fresh baseline" },
  { value: "A_prime", label: "A′ · Exact replay" },
  { value: "B", label: "B · With resolver" },
] satisfies { value: RunLabel; label: string }[];

beforeEach(() => {
  motionPreference.reduced = false;
  vi.stubGlobal("PointerEvent", MouseEvent);
});
afterEach(() => { vi.unstubAllGlobals(); });

function Selection({ label = "Inspect Run" }: { label?: string }) {
  const [value, setValue] = useState<RunLabel>("A");
  return <ResearchRunSwitch label={label} value={value} options={options} onChange={setValue} />;
}

it("keeps native keyboard activation and updates the pressed condition immediately", async () => {
  const user = userEvent.setup();
  render(<Selection />);
  const group = screen.getByRole("group", { name: "Inspect Run" });
  const baseline = within(group).getByRole("button", { name: "A · Fresh baseline" });
  const replay = within(group).getByRole("button", { name: "A′ · Exact replay" });
  const resolved = within(group).getByRole("button", { name: "B · With resolver" });
  await user.tab();
  expect(baseline).toHaveFocus();
  await user.tab();
  expect(replay).toHaveFocus();
  await user.keyboard(" ");
  expect(replay).toHaveAttribute("aria-pressed", "true");
  expect(baseline).toHaveAttribute("aria-pressed", "false");
  await user.tab();
  await user.keyboard("{Enter}");
  expect(resolved).toHaveFocus();
  expect(resolved).toHaveAttribute("aria-pressed", "true");
  expect(replay).toHaveAttribute("aria-pressed", "false");
});

it("does not reset the current research context when its selected condition is clicked again", () => {
  const onChange = vi.fn();
  render(<ResearchRunSwitch label="Inspect Run" value="A" options={options} onChange={onChange} />);
  fireEvent.click(screen.getByRole("button", { name: "A · Fresh baseline" }));
  expect(onChange).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "B · With resolver" }));
  expect(onChange).toHaveBeenCalledExactlyOnceWith("B");
});

it("retains instant independent condition selection with reduced motion", () => {
  motionPreference.reduced = true;
  render(<><Selection label="Configuration" /><Selection label="Recorded graph" /></>);
  const configuration = screen.getByRole("group", { name: "Configuration" });
  const graph = screen.getByRole("group", { name: "Recorded graph" });
  fireEvent.click(within(configuration).getByRole("button", { name: "B · With resolver" }));
  expect(within(configuration).getByRole("button", { name: "B · With resolver" })).toHaveAttribute("aria-pressed", "true");
  expect(within(graph).getByRole("button", { name: "A · Fresh baseline" })).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(within(graph).getByRole("button", { name: "A′ · Exact replay" }));
  expect(within(graph).getByRole("button", { name: "A′ · Exact replay" })).toHaveAttribute("aria-pressed", "true");
  expect(within(configuration).getByRole("button", { name: "B · With resolver" })).toHaveAttribute("aria-pressed", "true");
});
