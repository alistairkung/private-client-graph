import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ViewSwitch } from "./ViewSwitch";

const preferences = vi.hoisted(() => ({ reduced: true }));
vi.mock("motion/react", async (importOriginal) => ({
  ...(await importOriginal<typeof import("motion/react")>()),
  useReducedMotion: () => preferences.reduced,
}));
class TestPointerEvent extends MouseEvent {
  readonly pointerId: number;
  readonly isPrimary: boolean;
  constructor(type: string, init: PointerEventInit = {}) {
    super(type, init);
    this.pointerId = init.pointerId ?? 1;
    this.isPrimary = init.isPrimary ?? true;
  }
}
beforeEach(() => {
  vi.stubGlobal("PointerEvent", TestPointerEvent);
  Object.defineProperties(HTMLElement.prototype, {
    setPointerCapture: { configurable: true, value: vi.fn() },
    hasPointerCapture: { configurable: true, value: () => true },
    releasePointerCapture: { configurable: true, value: vi.fn() },
  });
});
afterEach(() => {
  preferences.reduced = true;
  vi.unstubAllGlobals();
});
function Fixture({
  changed = vi.fn(),
  translated = false,
}: {
  changed?: (value: string) => void;
  translated?: boolean;
}) {
  const [value, setValue] = useState<"graph" | "list">("graph");
  return (
    <ViewSwitch
      value={value}
      onChange={(next) => {
        changed(next);
        setValue(next);
      }}
      label="Relationship view"
      options={[
        {
          value: "graph",
          label: translated ? "图谱" : "Graph",
          controls: "graph-panel",
        },
        {
          value: "list",
          label: translated ? "列表" : "List",
          controls: "list-panel",
        },
      ]}
    />
  );
}
function drag(track: HTMLElement, x: number) {
  fireEvent.pointerDown(track, {
    button: 0,
    pointerId: 1,
    isPrimary: true,
    clientX: 20,
  });
  fireEvent.pointerMove(track, { pointerId: 1, isPrimary: true, clientX: x });
}
describe("tactile accessible view switching", () => {
  it("keeps both choices clickable and supports roving arrows, Home/End and native Enter/Space", async () => {
    const changed = vi.fn();
    render(<Fixture changed={changed} />);
    await userEvent.click(screen.getByRole("tab", { name: "Graph" }));
    expect(changed).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("tab", { name: "List" }));
    expect(screen.getByRole("tab", { name: "List" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await userEvent.keyboard("{Home}");
    expect(screen.getByRole("tab", { name: "Graph" })).toHaveFocus();
    expect(screen.getByRole("tab", { name: "Graph" })).toHaveAttribute(
      "tabindex",
      "0",
    );
    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "List" })).toHaveFocus();
    await userEvent.keyboard("{ArrowLeft}{End}{Enter} ");
    expect(screen.getByRole("tab", { name: "List" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });
  it("previews dragging without committing, commits nearest once on release, and suppresses the trailing pointer click", () => {
    const changed = vi.fn();
    render(<Fixture changed={changed} />);
    const track = screen.getByRole("tablist");
    drag(track, 130);
    expect(changed).not.toHaveBeenCalled();
    expect(screen.getByRole("tab", { name: "Graph" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    fireEvent.pointerUp(track, { pointerId: 1, clientX: 130 });
    expect(changed).toHaveBeenCalledExactlyOnceWith("list");
    expect(screen.getByRole("tab", { name: "List" })).toHaveFocus();
    fireEvent.click(screen.getByRole("tab", { name: "Graph" }), { detail: 1 });
    expect(changed).toHaveBeenCalledTimes(1);
  });
  it("rolls back pointer cancellation and lost capture, then accepts keyboard activation instead of swallowing it", async () => {
    const changed = vi.fn();
    render(<Fixture changed={changed} />);
    const track = screen.getByRole("tablist");
    drag(track, 130);
    fireEvent.pointerCancel(track, { pointerId: 1 });
    expect(changed).not.toHaveBeenCalled();
    screen.getByRole("tab", { name: "List" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(changed).toHaveBeenCalledExactlyOnceWith("list");
    drag(track, -80);
    fireEvent.lostPointerCapture(track, { pointerId: 1 });
    expect(changed).toHaveBeenCalledTimes(1);
    await userEvent.keyboard("{Home}");
    expect(screen.getByRole("tab", { name: "Graph" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });
  it("handles backtracking and Escape without changing the committed panel", async () => {
    const changed = vi.fn();
    render(<Fixture changed={changed} />);
    const track = screen.getByRole("tablist");
    drag(track, 130);
    fireEvent.pointerMove(track, { pointerId: 1, clientX: 21 });
    fireEvent.pointerUp(track, { pointerId: 1, clientX: 21 });
    expect(changed).not.toHaveBeenCalled();
    drag(track, 130);
    fireEvent.keyDown(track, { key: "Escape" });
    fireEvent.pointerUp(track, { pointerId: 1, clientX: 130 });
    expect(changed).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("tab", { name: "List" }));
    expect(changed).toHaveBeenCalledExactlyOnceWith("list");
  });
  it("cancels an in-progress gesture on locale measurement and retains direct reduced-motion control", async () => {
    const changed = vi.fn();
    const { rerender } = render(<Fixture changed={changed} />);
    const track = screen.getByRole("tablist");
    drag(track, 130);
    rerender(<Fixture changed={changed} translated />);
    fireEvent.pointerUp(track, { pointerId: 1, clientX: 130 });
    expect(changed).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("tab", { name: "列表" }));
    expect(changed).toHaveBeenCalledExactlyOnceWith("list");
    await waitFor(() =>
      expect(
        (track.querySelector(".view-switch-pill") as HTMLElement)?.style
          .transform,
      ).toContain("72px"),
    );
  });
});
